# Android Forensic Acquisition Tool Implementation Plan

This plan outlines the architecture, changes, and verification steps for completing the forensic acquisition tool according to the user's detailed specifications.

## User Review Required

> [!WARNING]
> The database extractions (Contacts, SMS, Browser History, WhatsApp) require root permissions on the Android device/emulator. If root access (`su`) is not available, these extractions will be gracefully skipped with clear warnings logged in the `acquisition.log` as required by the specifications.

## Open Questions
No open questions at this stage. We have verified that the emulator is running and supports `sha256sum`.

## Proposed Changes

We will implement the remaining features component by component, using a structured and modular approach.

---

### Component 1: Environment & Dependency Setup
We will update `requirements.txt` with pinned versions and install them in the virtual environment.

#### [MODIFY] [requirements.txt](file:///d:/security_app/mobieaquire/requirements.txt)
- Pin required dependencies:
  ```text
  adb-shell[usb]==0.4.4
  pycryptodome==3.23.0
  jinja2==3.1.6
  pytest==8.4.0
  flake8==7.3.0
  python-dateutil==2.9.0
  ```

---

### Component 2: Device Communication & Detection
We will enhance `src/device.py` to auto-detect both USB and local TCP/IP emulators.

#### [MODIFY] [device.py](file:///d:/security_app/mobieaquire/src/device.py)
- Import `AdbDeviceTcp` and `AdbDeviceUsb`.
- Auto-detect mechanism:
  1. Try to connect via TCP (`127.0.0.1:5555`) for local emulators.
  2. If that fails, try to connect via USB.
- Support specifying the platform (`emulator` or `device`) via argument to bypass auto-detection.

---

### Component 3: CLI Parser & Investigator Confirmation
We will enhance the main entry point to parse all arguments using `argparse` and require interactive investigator confirmation.

#### [MODIFY] [acquire.py](file:///d:/security_app/mobieaquire/src/acquire.py)
- Expand `argparse` with:
  - `--output`: Parent directory for evidence folders (default: `output`).
  - `--platform`: Connection target (`emulator` or `device`).
  - `--skip`: Comma-separated list of artefacts to skip.
  - `--no-media`: Flag to skip media metadata extraction.
  - `--dry-run`: Flag to simulate acquisition.
- Auto-detect device and print metadata.
- Request investigator confirmation: `Proceed? (yes/no): ` before copying any evidence.
- Restructure folder creation to use the required `evidence_SERIAL_TIMESTAMP` format.

---

### Component 4: Extraction Engine Enhancements (Installed Apps, Databases, Media SHA256)
We will expand the extraction logic to retrieve all required artefacts and handle permissions gracefully.

#### [NEW] [parser.py](file:///d:/security_app/mobieaquire/src/parser.py)
- Implement `DumpsysPackageParser` to parse output of `dumpsys package`.
- Extract `versionName`, `firstInstallTime`, and `lastUpdateTime` for each app package.

#### [MODIFY] [extractor.py](file:///d:/security_app/mobieaquire/src/extractor.py)
- Refactor `extract_installed_apps` to call `dumpsys package` and run it through `DumpsysPackageParser`.
- Add database extraction helper:
  - Try direct pull using `adb-shell`'s `device.pull()`.
  - Fall back to copy via `su` if permissions allow, then pull.
  - Gracefully log skip reason if permission is denied.
- Extract `contacts2.db` (Call Log) to `artefacts/call_log/contacts2.db`.
- Extract `mmssms.db` (SMS) to `artefacts/sms/mmssms.db`.
- Extract Chrome history DB (Browser History) to `artefacts/browser_history/History`.
- Extract WhatsApp `msgstore.db.crypt15` and `key` (if accessible) to `artefacts/whatsapp/`.
- Enhance `extract_media_metadata`:
  - Run `find` and `stat` on-device to get path, size, and modification time.
  - Run `sha256sum` on-device to compute SHA256 for each media file.
  - Exclude `/storage/emulated/0/Android` path to prevent permission issues.
  - Return `media_metadata.json` saved in `artefacts/media_metadata/`.

---

### Component 5: Report Generation (HTML & JSON)
We will build a high-aesthetic responsive HTML report template and implement JSON machine-readable report generation.

#### [MODIFY] [reporter.py](file:///d:/security_app/mobieaquire/src/reporter.py)
- Implement `generate_json_report(output_dir, ...)` to write `report.json` with all metadata, counts, and files list.
- Read extracted metadata JSONs and build rich context for HTML template.

#### [MODIFY] [report.html.j2](file:///d:/security_app/mobieaquire/templates/report.html.j2)
- Re-design the report with modern responsive styling:
  - Custom Inter typography, harmonious deep blue and dark mode theme.
  - Cover section, Case and Investigator details.
  - Timestamps, integrity verification section.
  - Clean cards and interactive tables for installed apps, call logs, SMS logs, and media metadata.
  - Forensic footer with tool details and signatures.

---

### Component 6: Chain of Custody & Integrity Verification
We will implement the manifest creation and directory-wide hashing.

#### [MODIFY] [hasher.py](file:///d:/security_app/mobieaquire/src/hasher.py)
- Update `EvidenceHasher` to hash evidence files.
- Create `integrity/acquisition_hash.txt` listing SHA256 and relative path for all evidence files.
- Compute and write SHA256 for the closed `acquisition.log`.

---

### Component 7: Testing Framework
We will implement 8+ tests to verify functionality without requiring a physical device.

#### [NEW] [test_parser.py](file:///d:/security_app/mobieaquire/tests/test_parser.py)
- Test `DumpsysPackageParser` using sample `dumpsys package` output.
- Add tests for device metadata parsers.

#### [NEW] [test_hasher.py](file:///d:/security_app/mobieaquire/tests/test_hasher.py)
- Test SHA256 file hashing, manifest writing, and directory hash verification.

#### [NEW] [test_reporter.py](file:///d:/security_app/mobieaquire/tests/test_reporter.py)
- Test JSON report generation.
- Test HTML report generation with mock context.

---

### Component 8: Documentation & Repository Tagging
We will write a comprehensive `README.md` and perform git tagging.

#### [MODIFY] [README.md](file:///d:/security_app/mobieaquire/README.md)
- Complete user manual including project description, setup, CLI flags, output structure, design decisions, and limitations.

---

## Verification Plan

### Automated Tests
We will execute our unit tests using pytest from the virtual environment:
```bash
.\venv\Scripts\pytest tests/
```

### Manual Verification
1. Run a dry-run test acquisition:
   ```bash
   .\venv\Scripts\python src/acquire.py --case CASE-001 --investigator "John Doe" --dry-run
   ```
2. Run a full acquisition on the active emulator:
   ```bash
   .\venv\Scripts\python src/acquire.py --case CASE-001 --investigator "John Doe" --platform emulator
   ```
3. Inspect the created `evidence_SERIAL_TIMESTAMP` directory to confirm structure, HTML layout aesthetics, and integrity files.
