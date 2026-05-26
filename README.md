# Android Forensic Acquisition Tool

A forensically sound, automated command-line acquisition tool for Android devices and emulators. It connects to the target via ADB (either USB or TCP/IP) and extracts key artefacts (installed apps, call logs, SMS, browser history, WhatsApp, and external storage metadata) with cryptographic integrity checks.

---

## Features

- **Device Connection & Detection**: Automatically detects local TCP/IP emulators (`127.0.0.1:5555`) or USB devices. Can also target a specific platform using `--platform`.
- **Artefact Extraction**:
  - Installed apps metadata parsed from `dumpsys package` (includes version, first install time, and last update time).
  - Contacts / Call Logs (`contacts2.db`).
  - SMS Messages (`mmssms.db`).
  - Browser History (Chrome `History` database).
  - WhatsApp databases (`msgstore.db`) and encryption keys.
  - External storage file list with path, size, modification time, and SHA-256 hashes calculated on-device.
- **Root Fallback Mechanism**: Gracefully handles permissions by trying direct pull first, then falling back to copying via `su` (if root access is available). If root is not available, these extractions are gracefully skipped with warnings.
- **Investigator Confirmation**: Interactively displays target device metadata and destinations, asking for approval (`Proceed? yes/no`) before making modifications.
- **Dry-Run Simulation**: Supports testing without creating output folders or pulling data using the `--dry-run` flag.
- **Integrity Verification**: Generates a JSON manifest and a standard `acquisition_hash.txt` listing SHA-256 signatures of all evidence files (including reports and the closed `acquisition.log`).
- **Forensic Report**: Generates high-aesthetic HTML and JSON reports containing case information, target device metadata, tabbed interactive evidence logs, and file integrity manifests.

---

## Setup & Installation

1. **Virtual Environment**:
   Ensure you have Python 3.11+ installed. Set up and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Dependencies**:
   Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prerequisites**:
   - Ensure the Android device / emulator is running and connected (for emulators, TCP/IP port `5555` should be open).
   - Ensure ADB keys are generated on the host system (typically in `~/.android/adbkey`).

---

## CLI Usage

Run the tool using the virtual environment python interpreter:

```bash
.\venv\Scripts\python src/acquire.py --case <CASE_ID> --investigator <INVESTIGATOR_NAME> [flags]
```

### Command Line Flags

| Flag | Type | Description |
|---|---|---|
| `--case` | String (Required) | Unique identifier for the current investigation case. |
| `--investigator` | String (Required) | Name/ID of the lead investigator. |
| `--output` | String | Parent directory for writing evidence folders (default: `output`). |
| `--platform` | String | Explicit target connection mode: `emulator` (TCP/IP) or `device` (USB). |
| `--skip` | String | Comma-separated list of artefacts to skip (e.g. `sms,whatsapp`). |
| `--no-media` | Flag | Skip media metadata collection. |
| `--dry-run` | Flag | Simulate the acquisition flow. Logs metadata and steps but does not write files. |

### Example Commands

- **Dry-run simulation**:
  ```bash
  .\venv\Scripts\python src/acquire.py --case CASE-001 --investigator "John Doe" --dry-run
  ```

- **Full TCP emulator acquisition**:
  ```bash
  .\venv\Scripts\python src/acquire.py --case CASE-001 --investigator "John Doe" --platform emulator
  ```

---

## Output Structure

The tool creates a forensically structured folder: `evidence_<SERIAL>_<TIMESTAMP>` inside the output parent folder:

```text
evidence_EMULATOR36X5X11X0_20260526_152500/
├── device_info.json
├── installed_apps.json
├── acquisition.log
├── manifest.json
├── report.html
├── report.json
├── artefacts/
│   ├── call_log/
│   │   └── contacts2.db
│   ├── sms/
│   │   └── mmssms.db
│   ├── browser_history/
│   │   └── History
│   ├── whatsapp/
│   │   ├── msgstore.db
│   │   └── key
│   └── media_metadata/
│       └── media_metadata.json
└── integrity/
    └── acquisition_hash.txt
```

---

## Integrity Hashing

The `integrity/acquisition_hash.txt` file uses the standard `sha256sum` layout:

```text
<sha256_hash>  <relative_file_path>
```

It contains signatures for **all** files written to the acquisition directory (including the final generated HTML/JSON reports and the closed `acquisition.log`).

---

## Design Decisions

- **Performance**: Rather than executing separate ADB commands for each file or app, the tool dumps and parses `dumpsys package` as a single stream and executes an on-device shell loop using `find` and `stat`/`sha256sum` to complete scanning and hashing in one round-trip.
- **Forensic Soundness**: The logger operates in append-only mode. Once all operations are finished, the log file is hashed and recorded in the integrity verification manifest, sealing the acquisition logs.
- **Readability**: The HTML report uses an Outfit and JetBrains Mono typography layout with a sleek glassmorphism theme, tabbed view panels, and database query parsers to present active details cleanly.

---

## Limitations

- **Root Restrictions**: Extracting SQLite databases for Contacts, SMS, Browser history, and WhatsApp requires root privileges (`su`) on the target. If root access is missing, these items are skipped with warnings.
- **WhatsApp Encryption**: Modern WhatsApp databases may be encrypted on newer OS releases. If decryption keys are not accessible in the standard directories, only encrypted stores will be pulled.
