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

    args = parser.parse_args()

    print("\n=== Android Acquisition Tool ===")
    print(
        f"Investigator: {args.investigator}"
    )
    print(
        f"Case ID: {args.case}"
    )
    print()

    output_dir = (
        Path("output") /
        args.case
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    logger = AcquisitionLogger(
        output_dir /
        "acquisition.log"
    )

    logger.info(
        f"Investigator: {args.investigator}"
    )

    logger.info(
        f"Case ID: {args.case}"
    )

    phone = AndroidDevice()

    print("Connecting...")

    phone.connect()

    logger.info(
        "Device connected"
    )

    metadata = (
        phone.get_metadata()
    )

    device_info_path = (
        output_dir /
        "device_info.json"
    )

    with open(
        device_info_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4
        )

    hasher = EvidenceHasher()

    manifest = {}

    manifest[
        "device_info.json"
    ] = (
        hasher.hash_file(
            device_info_path
        )
    )

    extractor = (
        AndroidExtractor(
            phone,
            logger
        )
    )

    apps_path = (
        extractor
        .extract_installed_apps(
            output_dir
        )
    )

    manifest[
        "installed_apps.json"
    ] = (
        hasher.hash_file(
            apps_path
        )
    )

    media_path = (
        extractor
        .extract_media_metadata(
            output_dir
        )
    )

    manifest[
        "media_metadata.json"
    ] = (
        hasher.hash_file(
            media_path
        )
    )

    manifest_path = (
        output_dir /
        "manifest.json"
    )

    hasher.write_manifest(
        manifest_path,
        manifest
    )

    reporter = ReportGenerator(
        "templates"
    )

    reporter.generate(
        output_dir,
        args.case,
        args.investigator
    )

    print(
        "Report generated"
    )

    logger.info(
        "Acquisition completed"
    )

    print(
        "\nAcquisition complete."
    )

    print(
        f"Output: {output_dir}"
    )


if __name__ == "__main__":
    main()