## What

<!-- New build / shader fix / simulator / scripts ... -->

## New head-unit build (delete if not applicable)

- Build id: `hu-...`
- PSdZData / I-level / HMI version:
- [ ] `tools/port-build.py verify --build <id> --rootfs <rootfs>` says OK
- [ ] boots to the home screen; controller keys and touch work
- [ ] `status` and `verified` filled in `build.json`
- [ ] `signatures.json` generated from this build
- [ ] PORT-REPORT.md: remaining FAILED items explained

## Always

- [ ] `python3 -m unittest discover -s tests` passes
- [ ] no firmware files, extracted rootfs content, VINs, coding backups or other personal data
