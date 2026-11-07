#!/usr/bin/env python3
"""Capture a bounded native HmiMain3D startup through the ANGLE provider."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
import re
import shutil
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


QEMU_REGISTERS = {
    "dispc_control": 0x58001040,
    "lcd_size": 0x5800107C,
    "lcd2_size": 0x580013CC,
    "lcd3_size": 0x58001834,
    "gfx_base": 0x58001080,
    "gfx_position": 0x58001088,
    "gfx_size": 0x5800108C,
    "gfx_attributes": 0x580010A0,
}


def qmp_command(stream, name, arguments=None):
    request = {"execute": name}
    if arguments is not None:
        request["arguments"] = arguments
    stream.write((json.dumps(request) + "\r\n").encode())
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError(f"QMP closed while executing {name}")
        response = json.loads(line)
        if "return" not in response and "error" not in response:
            continue
        if "error" in response:
            raise RuntimeError(f"QMP {name}: {response['error']}")
        return response["return"]


def wait_for_marker(path, marker, timeout):
    deadline = time.monotonic() + timeout
    marker_bytes = marker.encode()
    offset = 0
    pending = b""
    while time.monotonic() < deadline:
        try:
            with path.open("rb") as stream:
                if path.stat().st_size < offset:
                    offset = 0
                    pending = b""
                stream.seek(offset)
                lines = (pending + stream.read()).split(b"\n")
                offset = stream.tell()
            pending = lines.pop()
            if any(marker_bytes in line and not line.lstrip(b" \t\r\0").startswith(b"+ ")
                   for line in lines):
                return
        except FileNotFoundError:
            pass
        time.sleep(0.25)
    raise TimeoutError(f"did not see {marker!r} in {path} within {timeout}s")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class HrefCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def capture_hmi_inspector(base_url, evidence_dir):
    """Save the inspector's route index and read-only graphics views."""
    base_url = base_url.rstrip("/")
    parsed_base = urlparse(base_url)
    records = []

    def request(label, url, method="GET"):
        request_started = time.monotonic()
        record = {"label": label, "url": url, "method": method}
        try:
            req = Request(url, data=b"" if method == "POST" else None, method=method)
            with urlopen(req, timeout=30) as response:
                body = response.read(8 * 1024 * 1024 + 1)
                truncated = len(body) > 8 * 1024 * 1024
                body = body[:8 * 1024 * 1024]
                content_type = response.headers.get("Content-Type")
                status = response.status
        except HTTPError as error:
            body = error.read(8 * 1024 * 1024 + 1)
            truncated = len(body) > 8 * 1024 * 1024
            body = body[:8 * 1024 * 1024]
            content_type = error.headers.get("Content-Type")
            status = error.code
            record["error"] = str(error)
        except (URLError, TimeoutError, OSError) as error:
            record["error"] = str(error)
            record["elapsed_seconds"] = round(time.monotonic() - request_started, 3)
            records.append(record)
            return b""

        suffix = "html" if not content_type or "html" in content_type.lower() else "bin"
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("_.") or "page"
        output = evidence_dir / f"inspector-{safe_label}.{suffix}"
        output.write_bytes(body)
        record.update({
            "status": status,
            "content_type": content_type,
            "path": output.name,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "truncated_at_8_mib": truncated,
            "elapsed_seconds": round(time.monotonic() - request_started, 3),
        })
        records.append(record)
        return body

    index = request("index-post", base_url + "/", "POST")
    parser = HrefCollector()
    try:
        parser.feed(index.decode("utf-8", errors="replace"))
    except Exception as error:
        records.append({"label": "index-parse", "error": str(error)})

    routes = []
    allowed_roots = {"widgets", "scenegraph", "appearances", "gfxinfo", "graphicsinfo"}
    for href in parser.hrefs:
        target = urljoin(base_url + "/", href)
        parsed = urlparse(target)
        if (parsed.scheme, parsed.netloc) != (parsed_base.scheme, parsed_base.netloc):
            continue
        if parsed.path.strip("/").split("/", 1)[0].lower() not in allowed_roots:
            continue
        if target not in routes:
            routes.append(target)
    if not routes:
        routes = [base_url + "/" + route for route in
                  ("Widgets", "SceneGraph", "Appearances", "GfxInfo")]

    for target in routes[:12]:
        parsed = urlparse(target)
        route = parsed.path.strip("/") or "root"
        label = re.sub(r"[^A-Za-z0-9_.-]+", "_", route)
        # Keep filenames stable and collision-free when pointers appear in paths.
        label = f"{label[:48]}-{hashlib.sha256(target.encode()).hexdigest()[:8]}"
        request(label, target)

    return {
        "base_url": base_url,
        "index_method": "POST",
        "routes_discovered": routes,
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial-log", type=Path, required=True)
    parser.add_argument("--host-log", type=Path, required=True)
    parser.add_argument("--network-pcap", type=Path)
    parser.add_argument(
        "--run-manifest",
        type=Path,
        help="pre-QEMU profile manifest used to launch this guest",
    )
    parser.add_argument(
        "--otf-stream",
        type=Path,
        help="copy the connected BMW OTF viewer stream into the evidence bundle",
    )
    parser.add_argument(
        "--otf-client-log",
        type=Path,
        help="copy the run-correlated host OTF connection log",
    )
    parser.add_argument("--shader-capture-dir", type=Path)
    parser.add_argument("--resource-capture-dir", type=Path)
    parser.add_argument(
        "--hmi-inspector-base-url",
        help="optional forwarded HMI inspector URL; captures its route list and read-only graphics pages",
    )
    parser.add_argument("--qmp-socket", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument(
        "--start-marker",
        default="Starting HmiMain3D directly after Screen is ready",
    )
    parser.add_argument("--wait-seconds", type=float, default=900)
    parser.add_argument(
        "--capture-after-seconds",
        type=float,
        default=900,
        help="host wall-clock seconds after the launch marker before the snapshot (default: 900 for QEMU TCG)",
    )
    parser.add_argument(
        "--capture-after-marker",
        help="capture after this marker appears in the guest serial log instead of using a fixed host delay",
    )
    parser.add_argument("--keep-guest-running", action="store_true")
    args = parser.parse_args()

    run_manifest = None
    if args.run_manifest:
        run_manifest = json.loads(args.run_manifest.read_text())
        if run_manifest.get("schema") != "idrive6-hmi-run-manifest-v1":
            parser.error(f"unsupported run manifest: {args.run_manifest}")

    wait_for_marker(args.serial_log, args.start_marker, args.wait_seconds)
    started = time.monotonic()
    start_utc = datetime.now(timezone.utc).isoformat()
    if args.capture_after_marker:
        wait_for_marker(
            args.serial_log, args.capture_after_marker, args.wait_seconds
        )
    else:
        time.sleep(args.capture_after_seconds)

    args.evidence_dir.mkdir(parents=True, exist_ok=False)
    serial_copy = args.evidence_dir / "serial.log"
    host_copy = args.evidence_dir / "angle-egl-rpc-server.log"
    network_pcap_copy = (
        args.evidence_dir / "network.pcap" if args.network_pcap else None
    )
    otf_stream_copy = (
        args.evidence_dir / "otf-viewer-stream.bin" if args.otf_stream else None
    )
    otf_client_log_copy = (
        args.evidence_dir / "otf-client.log" if args.otf_client_log else None
    )
    shutil.copy2(args.serial_log, serial_copy)
    shutil.copy2(args.host_log, host_copy)
    run_manifest_copy = None
    if args.run_manifest:
        run_manifest_copy = args.evidence_dir / "run-manifest.json"
        shutil.copy2(args.run_manifest, run_manifest_copy)
    if network_pcap_copy is not None:
        shutil.copy2(args.network_pcap, network_pcap_copy)
    if otf_stream_copy is not None:
        shutil.copy2(args.otf_stream, otf_stream_copy)
    if otf_client_log_copy is not None:
        shutil.copy2(args.otf_client_log, otf_client_log_copy)
    shader_capture_copy = None
    if args.shader_capture_dir and args.shader_capture_dir.exists():
        shader_capture_copy = args.evidence_dir / "shader-captures"
        shutil.copytree(args.shader_capture_dir, shader_capture_copy)
    resource_capture_copy = None
    if args.resource_capture_dir and args.resource_capture_dir.exists():
        resource_capture_copy = args.evidence_dir / "resource-captures"
        shutil.copytree(args.resource_capture_dir, resource_capture_copy)
    serial_text = serial_copy.read_text(errors="replace")
    host_text = host_copy.read_text(errors="replace")
    run_id_markers = sorted(set(re.findall(
        r"^IDRIVE_HMI_RUN_ID=([A-Za-z0-9_.-]+)$", serial_text, re.MULTILINE
    )))
    rpc_run_id_markers = sorted(set(re.findall(
        r"^ANGLE_EGL_RPC_RUN_ID id=([A-Za-z0-9_.-]+)$", host_text, re.MULTILINE
    )))
    otf_client_run_id = None
    if otf_client_log_copy is not None:
        for line in otf_client_log_copy.read_text(errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("event") == "run_context":
                otf_client_run_id = record.get("run_id")
                break
    rpc_records = [
        line for line in host_text.splitlines()
        if line.startswith("ANGLE_EGL_RPC ")
    ]
    unsupported = [
        line for line in serial_text.splitlines()
        if "IDRIVE_ANGLE_UNSUPPORTED_GLES " in line
    ]
    gles_trace = [
        line for line in serial_text.splitlines()
        if line.startswith((
            "IDRIVE_ANGLE_GLES_CALL ",
            "IDRIVE_ANGLE_GLES_DONE ",
        ))
    ]
    provider_trace = [
        line for line in serial_text.splitlines()
        if any(token in line for token in (
            "IDRIVE_ANGLE_PROVIDER_",
            "IDRIVE_ANGLE_EGL_CALL ",
            "IDRIVE_ANGLE_RPC_",
        ))
    ]
    process_exit_lines = [
        line for line in serial_text.splitlines()
        if "HmiMain3D exited with status" in line
    ]
    serial_lines = serial_text.splitlines()
    diagnostic_blocks = []
    current_diagnostic = None
    for line in serial_lines:
        if line.startswith("HMI_DIAGNOSTIC_BEGIN "):
            if current_diagnostic is not None:
                diagnostic_blocks.append(current_diagnostic)
            match = re.fullmatch(
                r"HMI_DIAGNOSTIC_BEGIN t\+(\d+)s ([a-z]+)", line
            )
            current_diagnostic = {
                "sample_seconds": int(match.group(1)) if match else None,
                "kind": match.group(2) if match else "unknown",
                "complete": False,
                "lines": [],
            }
        elif line.startswith("HMI_DIAGNOSTIC_END "):
            if current_diagnostic is not None:
                current_diagnostic["complete"] = True
                diagnostic_blocks.append(current_diagnostic)
            current_diagnostic = None
        elif current_diagnostic is not None:
            current_diagnostic["lines"].append(line)
    if current_diagnostic is not None:
        diagnostic_blocks.append(current_diagnostic)

    def diagnostic_lines(kind):
        lines = []
        for block in diagnostic_blocks:
            if block["kind"] == kind:
                lines.extend(block["lines"])
        return lines

    hmi_backtrace = diagnostic_lines("back")
    hmi_thread_state = diagnostic_lines("threads")
    hmi_process_times = diagnostic_lines("times")
    hmi_process_args = diagnostic_lines("arguments") + diagnostic_lines("args")
    hmi_module_map = diagnostic_lines("mapinfo")
    hmi_process_fds = diagnostic_lines("fds")
    hmi_system_log = diagnostic_lines("slog")
    incomplete_diagnostics = [
        {
            "sample_seconds": block["sample_seconds"],
            "kind": block["kind"],
            "captured_line_count": len(block["lines"]),
        }
        for block in diagnostic_blocks
        if not block["complete"]
    ]
    hmi_process_state = [
        line for line in serial_lines
        if "HmiMain3D exec PID remains alive at " in line or
        "HmiMain3D exec PID is no longer running at " in line
    ]

    manifest = {
        "run_id": run_manifest.get("run_id") if run_manifest else None,
        "run_id_serial_markers": run_id_markers,
        "run_id_rpc_markers": rpc_run_id_markers,
        "run_id_otf_client_log": otf_client_run_id,
        "run_id_matches_run_manifest": (
            run_id_markers == [run_manifest.get("run_id")]
            if run_manifest and run_manifest.get("run_id") else None
        ),
        "rpc_run_id_matches_run_manifest": (
            rpc_run_id_markers == [run_manifest.get("run_id")]
            if run_manifest and run_manifest.get("run_id") else None
        ),
        "otf_run_id_matches_run_manifest": (
            otf_client_run_id == run_manifest.get("run_id")
            if run_manifest and run_manifest.get("run_id") else None
        ),
        "run_manifest": (
            {
                "path": run_manifest_copy.name,
                "sha256": sha256(run_manifest_copy),
                "bytes": run_manifest_copy.stat().st_size,
            }
            if run_manifest_copy is not None else None
        ),
        "start_marker": args.start_marker,
        "capture_started_utc": start_utc,
        "capture_after_seconds": args.capture_after_seconds,
        "capture_after_marker": args.capture_after_marker,
        "serial_log": serial_copy.name,
        "serial_log_sha256": sha256(serial_copy),
        "host_log": host_copy.name,
        "host_log_sha256": sha256(host_copy),
        "network_pcap": (
            {
                "path": network_pcap_copy.name,
                "sha256": sha256(network_pcap_copy),
                "bytes": network_pcap_copy.stat().st_size,
            }
            if network_pcap_copy is not None else None
        ),
        "otf_stream": (
            {
                "path": otf_stream_copy.name,
                "sha256": sha256(otf_stream_copy),
                "bytes": otf_stream_copy.stat().st_size,
            }
            if otf_stream_copy is not None else None
        ),
        "otf_client_log": (
            {
                "path": otf_client_log_copy.name,
                "sha256": sha256(otf_client_log_copy),
                "bytes": otf_client_log_copy.stat().st_size,
            }
            if otf_client_log_copy is not None else None
        ),
        "shader_captures": (
            [
                {
                    "path": path.relative_to(args.evidence_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
                for path in sorted(shader_capture_copy.iterdir())
                if path.is_file()
            ]
            if shader_capture_copy is not None else []
        ),
        "resource_captures": (
            [
                {
                    "path": path.relative_to(args.evidence_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
                for path in sorted(resource_capture_copy.iterdir())
                if path.is_file()
            ]
            if resource_capture_copy is not None else []
        ),
        "rpc_record_count": len(rpc_records),
        "rpc_records": rpc_records,
        "unsupported_gles_calls": unsupported,
        "first_unsupported_gles_call": unsupported[0] if unsupported else None,
        "gles_trace": gles_trace,
        "provider_trace_count": len(provider_trace),
        "provider_trace": provider_trace,
        "hmi_exit_lines": process_exit_lines,
        "hmi_process_state": hmi_process_state,
        "hmi_diagnostic_blocks": diagnostic_blocks,
        "incomplete_diagnostics": incomplete_diagnostics,
        "hmi_thread_state": hmi_thread_state,
        "hmi_process_times": hmi_process_times,
        "hmi_process_args": hmi_process_args,
        "hmi_process_fds": hmi_process_fds,
        "hmi_system_log": hmi_system_log,
        "hmi_backtrace": hmi_backtrace,
        "hmi_module_map": hmi_module_map,
        "hmi_start_markers": [
            line for line in serial_text.splitlines()
            if ("HmiMain3D" in line or "ANGLE_UNSUPPORTED_GLES" in line or
                "IDRIVE_ANGLE_PROVIDER_" in line or
                "IDRIVE_ANGLE_EGL_CALL " in line)
        ],
        "dss_registers": {},
        "display_capture": "display.ppm",
        "guest_shutdown_after_capture": not args.keep_guest_running,
    }

    if args.hmi_inspector_base_url:
        manifest["hmi_inspector"] = capture_hmi_inspector(
            args.hmi_inspector_base_url, args.evidence_dir
        )

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as qmp:
        qmp.settimeout(20)
        qmp.connect(str(args.qmp_socket))
        stream = qmp.makefile("rwb", buffering=0)
        manifest["qmp_greeting"] = json.loads(stream.readline())
        qmp_command(stream, "qmp_capabilities")
        manifest["qmp_status"] = qmp_command(stream, "query-status")
        manifest["user_network_info"] = qmp_command(stream, "human-monitor-command", {
            "command-line": "info usernet"
        })
        manifest["network_info"] = qmp_command(stream, "human-monitor-command", {
            "command-line": "info network"
        })
        qmp_command(stream, "screendump", {
            "filename": str(args.evidence_dir / "display.ppm")
        })
        for name, address in QEMU_REGISTERS.items():
            output = qmp_command(stream, "human-monitor-command", {
                "command-line": f"xp /1wx 0x{address:08x}"
            })
            match = re.search(r":\s*(0x[0-9a-fA-F]+)", output)
            manifest["dss_registers"][name] = {
                "address": f"0x{address:08x}",
                "value": int(match.group(1), 16) if match else None,
                "monitor_output": output.strip(),
            }
        if not args.keep_guest_running:
            qmp_command(stream, "quit")

    manifest["capture_elapsed_seconds"] = round(time.monotonic() - started, 3)
    manifest_path = args.evidence_dir / "hmi-startup.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "manifest": str(manifest_path),
        "run_id": manifest["run_id"],
        "run_id_matches_run_manifest": manifest["run_id_matches_run_manifest"],
        "rpc_run_id_matches_run_manifest": manifest["rpc_run_id_matches_run_manifest"],
        "otf_run_id_matches_run_manifest": manifest["otf_run_id_matches_run_manifest"],
        "network_pcap": (
            str(network_pcap_copy) if network_pcap_copy is not None else None
        ),
        "otf_stream": (
            str(otf_stream_copy) if otf_stream_copy is not None else None
        ),
        "resource_capture_count": len(manifest["resource_captures"]),
        "rpc_record_count": manifest["rpc_record_count"],
        "unsupported_gles_calls": unsupported,
        "gles_trace_count": len(gles_trace),
        "provider_trace_count": manifest["provider_trace_count"],
        "hmi_process_state": hmi_process_state,
        "hmi_diagnostic_block_count": len(diagnostic_blocks),
        "incomplete_diagnostics": incomplete_diagnostics,
        "hmi_backtrace": hmi_backtrace,
        "hmi_thread_state": hmi_thread_state,
        "hmi_process_args": hmi_process_args,
        "hmi_module_map": hmi_module_map,
        "hmi_system_log_line_count": len(hmi_system_log),
        "hmi_exit_lines": process_exit_lines,
        "display_capture": str(args.evidence_dir / "display.ppm"),
        "guest_shutdown_after_capture": manifest["guest_shutdown_after_capture"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
