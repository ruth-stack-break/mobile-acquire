"""
acquire.py

Forensic acquisition workflow.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

from src.device import AndroidDevice
from src.logger import AcquisitionLogger
from src.hasher import EvidenceHasher
from src.extractor import AndroidExtractor
from src.reporter import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Android Forensic Acquisition Tool"
    )

    parser.add_argument(
        "--investigator",
        required=True,
        help="Investigator name"
    )

    parser.add_argument(
        "--case",
        required=True,
        help="Case ID"
    )

    parser.add_argument(
        "--output",
        default="output",
        help="Parent directory for evidence folders"
    )

    parser.add_argument(
        "--platform",
        choices=["emulator", "device"],
        help="Connection target (emulator or device)"
    )

    parser.add_argument(
        "--skip",
        help="Comma-separated list of artefacts to skip"
    )

    parser.add_argument(
        "--no-media",
        action="store_true",
        help="Skip media metadata extraction"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate acquisition"
    )

    args = parser.parse_args()

    print("\n=== Android Acquisition Tool ===")
    print(f"Investigator: {args.investigator}")
    print(f"Case ID: {args.case}")
    print()

    # Parse skipped artefacts
    skipped_artefacts = []
    if args.skip:
        skipped_artefacts = [
            s.strip().lower() for s in args.skip.split(",") if s.strip()
        ]

    phone = AndroidDevice()
    print("Connecting...")
    try:
        phone.connect(platform=args.platform)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    print("Device connected successfully.")
    metadata = phone.get_metadata()
    print("\n--- Device Metadata ---")
    for k, v in metadata.items():
        print(f"{k.capitalize()}: {v}")
    print("-----------------------\n")

    # Generate timestamp and output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    serial = metadata.get("serial", "UNKNOWN").strip().replace(" ", "_")
    output_dir = Path(args.output) / f"evidence_{serial}_{timestamp}"
    print(f"Destination: {output_dir}\n")

    # Confirmation
    confirm = input("Proceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Acquisition aborted by investigator.")
        return

    if args.dry_run:
        print("\n--- DRY RUN: Simulating Acquisition ---")
        print("Connected to device successfully.")
        print(f"Would create output directory: {output_dir}")
        print("Simulated extractions:")
        if "apps" not in skipped_artefacts and "installed_apps" not in skipped_artefacts:
            print("  - Installed apps metadata")
        if "call_log" not in skipped_artefacts and "contacts" not in skipped_artefacts:
            print("  - Contacts/Call Log DB")
        if "sms" not in skipped_artefacts:
            print("  - SMS DB")
        if "browser_history" not in skipped_artefacts and "browser" not in skipped_artefacts:
            print("  - Chrome Browser History")
        if "whatsapp" not in skipped_artefacts:
            print("  - WhatsApp database/key")
        if "media" not in skipped_artefacts and not args.no_media:
            print("  - External storage (media) metadata")
        print("Simulation complete. No files written.")
        return

    # Real acquisition starts here
    output_dir.mkdir(parents=True, exist_ok=True)

    log_path = output_dir / "acquisition.log"
    logger = AcquisitionLogger(log_path)

    logger.info("Tool started")
    logger.info(f"Investigator: {args.investigator}")
    logger.info(f"Case ID: {args.case}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info("Device connected")
    logger.info(f"Device Metadata: {json.dumps(metadata)}")

    device_info_path = output_dir / "device_info.json"
    with open(device_info_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    hasher = EvidenceHasher()
    manifest = {}

    # Hash device info
    manifest["device_info.json"] = hasher.hash_file(device_info_path)

    extractor = AndroidExtractor(phone, logger)

    # 1. Apps Extraction
    if "apps" not in skipped_artefacts and "installed_apps" not in skipped_artefacts:
        apps_path = extractor.extract_installed_apps(output_dir)
        manifest["installed_apps.json"] = hasher.hash_file(apps_path)
    else:
        logger.info("Skipping installed apps extraction")

    # 2. Call Log Extraction
    if "call_log" not in skipped_artefacts and "contacts" not in skipped_artefacts:
        call_log_path = extractor.extract_call_log(output_dir)
        if call_log_path:
            manifest["artefacts/call_log/contacts2.db"] = hasher.hash_file(
                call_log_path
            )
    else:
        logger.info("Skipping call log extraction")

    # 3. SMS Extraction
    if "sms" not in skipped_artefacts:
        sms_path = extractor.extract_sms(output_dir)
        if sms_path:
            manifest["artefacts/sms/mmssms.db"] = hasher.hash_file(sms_path)
    else:
        logger.info("Skipping SMS extraction")

    # 4. Browser History Extraction
    if "browser_history" not in skipped_artefacts and "browser" not in skipped_artefacts:
        browser_path = extractor.extract_browser_history(output_dir)
        if browser_path:
            manifest["artefacts/browser_history/History"] = hasher.hash_file(
                browser_path
            )
    else:
        logger.info("Skipping browser history extraction")

    # 5. WhatsApp Extraction
    if "whatsapp" not in skipped_artefacts:
        whatsapp_paths = extractor.extract_whatsapp(output_dir)
        for path in whatsapp_paths:
            rel_path = path.relative_to(output_dir).as_posix()
            manifest[rel_path] = hasher.hash_file(path)
    else:
        logger.info("Skipping WhatsApp extraction")

    # 6. Media Metadata Extraction
    if "media" not in skipped_artefacts and not args.no_media:
        media_path = extractor.extract_media_metadata(output_dir)
        if media_path:
            manifest[
                "artefacts/media_metadata/media_metadata.json"
            ] = hasher.hash_file(media_path)
    else:
        logger.info("Skipping media metadata extraction")

    # Generate Reports
    reporter = ReportGenerator("templates")
    report_path = reporter.generate(
        output_dir=output_dir,
        case_id=args.case,
        investigator=args.investigator,
        manifest=manifest
    )
    print("Report generated")

    logger.info("Acquisition completed")

    # Calculate hashes for report and log after closing log entries
    report_json_path = output_dir / "report.json"
    if report_json_path.exists():
        manifest["report.json"] = hasher.hash_file(report_json_path)

    if report_path.exists():
        manifest["report.html"] = hasher.hash_file(report_path)

    # Hash the log itself
    manifest["acquisition.log"] = hasher.hash_file(log_path)

    # Write final manifest JSON
    manifest_path = output_dir / "manifest.json"
    hasher.write_manifest(manifest_path, manifest)

    # Write final acquisition_hash.txt in integrity folder
    hash_txt_path = output_dir / "integrity" / "acquisition_hash.txt"
    hasher.write_hash_file(hash_txt_path, manifest)

    print("\nAcquisition complete.")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()