"""
extractor.py

Android artefact extraction.
"""

import json
from pathlib import Path


class AndroidExtractor:
    """
    Handles artefact extraction.
    """

    def __init__(
        self,
        device,
        logger
    ):
        self.device = device
        self.logger = logger

    def extract_installed_apps(
        self,
        output_dir
    ):
        """
        Extract installed apps.
        """

        self.logger.info(
            "Extracting installed apps"
        )

        output_dir = Path(output_dir)

        apps_output = (
            output_dir /
            "installed_apps.json"
        )

        packages = self.device.shell(
            "pm list packages -f"
        )

        app_list = []

        for line in packages.splitlines():

            if "=" in line:
                path_part, package = (
                    line.replace(
                        "package:",
                        ""
                    ).rsplit("=", 1)
                )

                app_list.append(
                    {
                        "package":
                        package.strip(),

                        "apk_path":
                        path_part.strip()
                    }
                )

        with open(
            apps_output,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                app_list,
                file,
                indent=4
            )

        self.logger.info(
            "installed_apps.json created"
        )

        return apps_output

    def extract_media_metadata(
        self,
        output_dir
    ):
        """
        Extract /sdcard metadata.
        """

        self.logger.info(
            "Extracting media metadata"
        )

        output_dir = Path(output_dir)

        metadata_output = (
            output_dir /
            "media_metadata.json"
        )

        command = (
            "ls -lR /storage/emulated/0 | head -300"
        )

        result = self.device.shell(
            command
        )

        file_list = []

        current_dir = ""

        for line in result.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.endswith(":"):

                current_dir = (
                    line[:-1]
                )

                continue

            if (
                line.startswith("-")
                and current_dir
            ):

                parts = (
                    line.split()
                )

                if len(parts) >= 6:

                    size = parts[4]

                    filename = (
                        " ".join(
                            parts[7:]
                        )
                    )

                    path = (
                        f"{current_dir}/{filename}"
                    )

                    modified = (
                        " ".join(
                            parts[5:7]
                        )
                    )

                    file_list.append(
                        {
                            "path": path,
                            "size": size,
                            "modified": modified
                        }
                    )

        with open(
            metadata_output,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                file_list,
                file,
                indent=4
            )

        self.logger.info(
            "media_metadata.json created"
        )

        return metadata_output