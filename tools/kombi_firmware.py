"""Stage the verified Bosch BO03 6WB graphics firmware from PSdZData."""

import hashlib
from dataclasses import dataclass
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET


VERSION = "007_003_005"


@dataclass(frozen=True)
class FlashImage:
    swfl: str
    base: int
    size: int
    sha256: str

    @property
    def filename(self):
        return f"swfl_{self.swfl}-{self.base:08x}.bin"


PROGRAM = FlashImage("00003e5b", 0xbf400000, 0x800000,
                     "4b45c960cd09b6427701a631a045b05bc9ce052b225a3591abd10bf899c6d9f0")
CONFIG = FlashImage("00003e5c", 0xbec00000, 0x800000,
                    "7b3c4242b49a911105027d9eda27820813a8ba502f65cccc3e26e273d8658b0d")
GRAPHICS = FlashImage("00003e5d", 0xbc000000, 0x2c00000,
                      "a3f5b9403f3f0f04fc3c592cd169158637cb0f797f08424ed695d15526856c92")


def decompress_nrv2b(source, size):
    """Decode the 8-bit NRV2B streams used by these flash segments."""
    pos = bits = remaining = 0
    output = bytearray()

    def byte():
        nonlocal pos
        if pos == len(source):
            raise ValueError("truncated NRV2B stream")
        value = source[pos]
        pos += 1
        return value

    def bit():
        nonlocal bits, remaining
        if not remaining:
            bits, remaining = byte(), 8
        remaining -= 1
        return (bits >> remaining) & 1

    def prefix(limit):
        value = 1
        while True:
            value = (value << 1) | bit()
            if value > limit:
                raise ValueError("NRV2B prefix exceeds bounds")
            if bit():
                return value

    distance = 1
    while True:
        while bit():
            if len(output) == size:
                raise ValueError("NRV2B literal exceeds segment size")
            output.append(byte())
        offset = prefix(0x1000002)
        if offset != 2:
            offset = (offset - 3) * 256 + byte()
            if offset == 0xffffffff:
                if len(output) != size or pos != len(source):
                    raise ValueError("NRV2B stream does not match segment size")
                return output
            distance = offset + 1

        length = 2 * bit() + bit()
        if not length:
            length = prefix(size) + 2
        length += 1 + (distance > 0xd00)
        if distance > len(output) or length > size - len(output):
            raise ValueError("NRV2B match exceeds segment bounds")
        if length <= distance:
            start = len(output) - distance
            output.extend(output[start:start + length])
        else:
            pattern = output[-distance:]
            output.extend((pattern * ((length + distance - 1) // distance))[:length])


def unpack_flash(package, manifest, image):
    if package.stat().st_size > image.size:
        raise ValueError("flash package exceeds expected image size")
    source = package.read_bytes()
    output = bytearray()
    previous_end = 0
    for segment in ET.parse(manifest).findall(".//{*}FLASH-SEGMENT"):
        start = int(segment.findtext("{*}SOURCE-START-ADDRESS", ""), 16)
        end = int(segment.findtext("{*}SOURCE-END-ADDRESS", ""), 16) + 1
        target = int(segment.findtext("{*}TARGET-START-ADDRESS", ""), 16)
        size = int(segment.findtext("{*}TARGET-END-ADDRESS", ""), 16) + 1 - target
        if (start != previous_end or not start < end <= len(source)
                or target != image.base + len(output) or not 0 < size <= image.size - len(output)):
            raise ValueError("unexpected flash segment bounds")
        payload = source[start:end]
        compression = segment.get("COMPRESSION-STATUS")
        if compression == "COMPRESSED" and segment.findtext("{*}COMPRESSION-METHOD") == "NRV":
            payload = decompress_nrv2b(payload, size)
        elif compression != "UNCOMPRESSED" or len(payload) != size:
            raise ValueError("unsupported flash segment encoding")
        output.extend(payload)
        previous_end = end
    if previous_end != len(source) or hashlib.sha256(output).hexdigest() != image.sha256:
        raise ValueError("unpacked image does not match the verified BO03 build")
    return output


def stage_kombi(psdzdata: Path, cache: Path):
    source = psdzdata / "swe/swfl"
    directory = cache / "firmware" / f"bo03-{VERSION}"
    directory.mkdir(parents=True, exist_ok=True)
    outputs = []
    for image in (PROGRAM, CONFIG, GRAPHICS):
        package = source / f"swfl_{image.swfl}.bin.{VERSION}"
        manifest = source / f"swfl_{image.swfl}.xml.{VERSION}"
        for path in (package, manifest):
            if not path.is_file():
                raise ValueError(f"Missing 6WB PSdZData file: {path}")
        output = directory / image.filename
        if output.is_file():
            with output.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() == image.sha256:
                    outputs.append(output)
                    continue
        try:
            data = unpack_flash(package, manifest, image)
        except (ET.ParseError, ValueError) as error:
            raise ValueError(f"Cannot unpack {package.name}: {error}") from error
        with tempfile.TemporaryDirectory(dir=directory) as temp:
            staged = Path(temp) / output.name
            staged.write_bytes(data)
            staged.replace(output)
        outputs.append(output)
    print(f"6WB firmware verified at {directory}", flush=True)
    return tuple(outputs)
