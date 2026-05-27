# Project Explanation & Interview Preparation Guide

This document explains the architecture, design choices, forensic concepts, and implementation details of the **Android Forensic Acquisition Tool**. It is designed to prepare you for technical interviews and project walkthroughs.

---

## 1. Project Overview

### What is this tool?
It is a **Forensic Acquisition Tool** built in Python that automates the collection of digital evidence from Android devices or emulators. It connects over ADB, extracts app metadata, call logs, SMS, browser history, WhatsApp databases, and media files, and generates a cryptographic chain-of-custody log, a manifest, and a polished HTML/JSON report.

### Why is it needed?
In digital forensics, acquiring data must be **reproducible, integrity-protected, and well-documented**. Manually running commands and copying databases introduces human error and risks modifying the evidence. This tool automates the process using forensically sound practices.

---

## 2. Technical Architecture & Implementation Details

Here is how each component works under the hood. You should refer to these source files when speaking:

### A. Host-Independent Communication: [device.py](file:///d:/security_app/mobieaquire/src/device.py)
* **How it works**: Uses the `adb-shell` Python library to communicate directly with the ADB protocol over USB or TCP/IP.
* **Why not use standard ADB command-line execution (`subprocess.run("adb shell ...")`)?**
  Using a subprocess requires the host machine to have the `adb` binary installed and set up in the system `PATH`. By using `adb-shell` with Python keys (`~/.android/adbkey`), the tool runs natively and platform-independently on any host OS (Windows, macOS, Linux) without requiring external dependencies.
* **Auto-Detection**: It tries connecting via TCP/IP first (IP `127.0.0.1:5555` for local emulators). If that fails, it falls back to USB connection.

### B. Root Permission Fallback Logic: [extractor.py](file:///d:/security_app/mobieaquire/src/extractor.py)
* **The Problem**: Databases like call logs (`contacts2.db`), SMS (`mmssms.db`), and browser history are stored in protected directory paths (e.g., `/data/data/...`) owned by their respective system apps. A non-root ADB shell cannot read or pull these files directly.
* **The Solution**: 
  1. The tool first attempts a **direct pull** of the database file.
  2. If that fails (due to permission denied), it checks if root permissions (`su`) are available on the device.
  3. If root is available, it executes a root-level copy on the device to clone the database to a temporary, readable directory: `/data/local/tmp/temp_db`.
  4. It changes permissions (`chmod 666`) of that temp copy so that the standard ADB user can read and pull it.
  5. It pulls the temp file to the host and then securely deletes (`rm -f`) the temp copy from the device.
  6. If root is not available, it skips extraction gracefully, warning the investigator and writing the warning to the audit log.

### C. Performance Optimization for Media Files: [extractor.py](file:///d:/security_app/mobieaquire/src/extractor.py)
* **The Problem**: A standard approach of finding media files, pulling them, or calling `sha256sum` in separate round-trips for 100+ files creates a bottleneck because of the overhead of running separate commands over the ADB bridge.
* **The Solution**: The tool executes a single, optimized shell pipeline on the device using `find`:
  ```bash
  find /storage/emulated/0 -path /storage/emulated/0/Android -prune -o -type f -exec sh -c 'for f; do stat -c "%n|%s|%Y" "$f" && sha256sum "$f"; done' _ {} +
  ```
  - **Pruning**: It explicitly prunes `/storage/emulated/0/Android` to avoid permission issues and OS system files.
  - **Execution**: The `-exec ... {} +` groups file paths and runs an on-device shell loop.
  - **Output**: For each file, it prints the format `path|size|mtime` on one line and the output of `sha256sum` on the next. The Python script parses this single string return, cutting down extraction time from minutes to under 2 seconds.

### D. Custom Stateful Parsing: [parser.py](file:///d:/security_app/mobieaquire/src/parser.py)
* **How it works**: Instead of running `dumpsys package` individually for each package (which takes over a minute for hundreds of packages), the tool runs the command once, capturing the entire device package dump. It uses `DumpsysPackageParser` (using stateful regular expression matching) to parse out package headers, `versionName`, `firstInstallTime`, and `lastUpdateTime` in milliseconds.

### E. Evidence Hashing & Closing Logs: [hasher.py](file:///d:/security_app/mobieaquire/src/hasher.py) & [acquire.py](file:///d:/security_app/mobieaquire/src/acquire.py)
* **How it works**: To verify integrity, we calculate the SHA-256 hash of every extracted file.
* **Log Hashing**: The `acquisition.log` records audit trails. It cannot be hashed while it is open, because writing the hash to the file would change the file itself.
* **The Solution**: 
  1. The tool finishes all extractions and logs "Acquisition completed".
  2. The log file is implicitly closed (since it is written in append-only format).
  3. The tool reads and hashes the closed `acquisition.log`, the `report.html`, and the `report.json`.
  4. It writes these hashes to the final `manifest.json` and the standard `integrity/acquisition_hash.txt` file. This seals the log, preventing subsequent alterations.

---

## 3. Forensic Soundness Concepts

An interviewer will likely ask you how you ensured **forensic soundness**:
1. **Write Blockers / Non-invasive Acquisition**: We do not write files or install agents on the target device. All operations are reads or temporary file copies in standard temp directories (`/data/local/tmp/`) which are cleaned up.
2. **Audit Trails**: Every action, command, connection result, and fallback step is written with UTC millisecond timestamps to an append-only audit log (`acquisition.log`).
3. **Chain of Custody**: Immediate hashing using SHA-256 of all output directories, saved in `integrity/acquisition_hash.txt` in standard `sha256sum` layout.
4. **Signatures**: The HTML report provides dedicated signature lines for the investigator and witness, linking the digital integrity to the physical chain of custody.

---

## 4. Key Interview Questions & Answers

### Q1: What makes your tool "forensically sound"?
**A**: Forensic soundness is about maintaining the integrity of the evidence and logging every action. My tool does this by:
- Operating read-only on target directories.
- Cleaning up device-side temp files immediately.
- Generating a detailed, timestamped audit log (`acquisition.log`) tracking every connection, command, and fallback execution.
- Hashing all files (including the audit log and report) using SHA-256 immediately after acquisition and saving them in a manifest file to verify they haven't been tampered with.

### Q2: Why did you write a custom shell pipeline for media files instead of using python's `os.walk` or pulling them?
**A**: Performance and efficiency. Pulling all files from a device takes massive network/USB bandwidth. Running individual ADB shell commands for each file introduces bridge round-trip latency. By sending a single nested `find` and `exec` loop, the device handles the work natively and returns a compact structured text stream containing paths, sizes, timestamps, and hashes. We parse it on the host in milliseconds.

### Q3: How does the database extraction fallback work?
**A**: Android isolates databases inside individual app sandbox directories (`/data/data/`). Standard user accounts cannot read these files. My tool:
1. Tries to pull the file directly (in case directories are configured otherwise or backup/debug flags are open).
2. If it gets a permission error, it checks if `su` (root access) is available.
3. If rooted, it uses `su root cp` to copy the database to `/data/local/tmp/temp_db`, calls `chmod 666` to make it world-readable, pulls it to the host, and deletes the temp copy on-device.
4. If not rooted, it logs a warning that the database extraction was skipped and continues gracefully.

### Q4: How is the HTML report generated? What technologies did you use?
**A**: The report is generated using **Jinja2 templates** with modern responsive styling. I used:
- **Python Sqlite3**: To query the pulled databases and extract the last 100 entries for calls, SMS, and browser history to populate interactive HTML tables.
- **Outfit & JetBrains Mono Fonts**: For a premium, readable aesthetic.
- **Responsive Flexbox/Grids & CSS Variable Theme**: Clean dark mode representation, tabbed explorer buttons, and verification tables showing cryptographic signatures.

### Q5: How did you write unit tests for a mobile acquisition tool when no physical device is connected to the testing server?
**A**: I implemented mocks and mock classes. For example:
- In `test_extractor.py`, I created a `DummyDevice` class that returns mock packages and command outputs.
- In `test_reporter.py`, I programmatically created a temporary sqlite database inside a temp folder, populated it with mock rows, and tested that the `ReportGenerator` was able to query the records, compute row counts, and generate HTML/JSON reports successfully.
