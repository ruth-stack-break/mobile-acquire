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

    def _device_file_exists(self, device_path):
        """
        Check if a file exists on the device, supporting root check.
        """
        try:
            res = self.device.shell(f"su root ls {device_path}")
            if "No such file" not in res and "not found" not in res and res.strip():
                return True
        except Exception:
            pass

        try:
            res = self.device.shell(f"ls {device_path}")
            if "No such file" not in res and "not found" not in res and res.strip():
                return True
        except Exception:
            pass

        return False

    def _pull_db_with_su_fallback(
        self,
        device_path,
        local_dest_path,
        temp_device_copy_path="/data/local/tmp/temp_db"
    ):
        """
        Tries to pull a database file directly. If that fails, attempts to use 'su'
        to copy it to a readable temporary location on device, pulls it from there,
        and cleans up.
        """
        local_dest_path = Path(local_dest_path)

        if not self._device_file_exists(device_path):
            self.logger.warn(f"Source file {device_path} does not exist on device.")
            return None

        # 1. Try direct pull
        try:
            self.logger.info(f"Attempting direct pull of {device_path}")
            local_dest_path.parent.mkdir(parents=True, exist_ok=True)
            self.device.device.pull(device_path, str(local_dest_path))
            self.logger.info(f"Direct pull of {device_path} succeeded")
            return local_dest_path
        except Exception as e:
            self.logger.warn(
                f"Direct pull of {device_path} failed: {e}. Trying su fallback..."
            )

        # 2. Try su copy fallback
        try:
            # Check if root access is available
            id_check = self.device.shell("su root id")
            if "uid=0" not in id_check and "root" not in id_check:
                self.logger.warn(
                    f"Root access (su) not available. Skipping {device_path}."
                )
                return None

            # Copy to a temporary location using su and make it readable
            self.device.shell(f"su root cp {device_path} {temp_device_copy_path}")
            self.device.shell(f"su root chmod 666 {temp_device_copy_path}")

            # Pull from temp location
            self.device.device.pull(temp_device_copy_path, str(local_dest_path))

            # Clean up on device
            self.device.shell(f"su root rm -f {temp_device_copy_path}")

            self.logger.info(f"Su copy pull of {device_path} succeeded")
            return local_dest_path
        except Exception as ex:
            self.logger.warn(f"Failed to pull {device_path} via su fallback: {ex}")
            try:
                self.device.shell(f"su root rm -f {temp_device_copy_path}")
            except Exception:
                pass
            return None

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

        # Get dumpsys package details
        dumpsys_raw = self.device.shell("dumpsys package")

        from src.parser import DumpsysPackageParser
        parser = DumpsysPackageParser()
        parsed_packages = parser.parse(dumpsys_raw)

        app_list = []

        for line in packages.splitlines():
            if "=" in line:
                path_part, package = (
                    line.replace(
                        "package:",
                        ""
                    ).rsplit("=", 1)
                )

                pkg_name = package.strip()
                apk_path = path_part.strip()

                pkg_info = parsed_packages.get(pkg_name, {
                    "versionName": "UNKNOWN",
                    "firstInstallTime": "UNKNOWN",
                    "lastUpdateTime": "UNKNOWN"
                })

                app_list.append(
                    {
                        "package": pkg_name,
                        "apk_path": apk_path,
                        "versionName": pkg_info["versionName"],
                        "firstInstallTime": pkg_info["firstInstallTime"],
                        "lastUpdateTime": pkg_info["lastUpdateTime"]
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

    def extract_call_log(self, output_dir):
        """
        Extract Contacts/Call Log DB.
        """
        self.logger.info("Extracting call log database")
        output_dir = Path(output_dir)
        dest_path = output_dir / "artefacts" / "call_log" / "contacts2.db"
        device_path = "/data/data/com.android.providers.contacts/databases/contacts2.db"
        return self._pull_db_with_su_fallback(device_path, dest_path)

    def extract_sms(self, output_dir):
        """
        Extract SMS DB.
        """
        self.logger.info("Extracting SMS database")
        output_dir = Path(output_dir)
        dest_path = output_dir / "artefacts" / "sms" / "mmssms.db"
        device_path = "/data/data/com.android.providers.telephony/databases/mmssms.db"
        return self._pull_db_with_su_fallback(device_path, dest_path)

    def extract_browser_history(self, output_dir):
        """
        Extract Chrome Browser History.
        """
        self.logger.info("Extracting browser history")
        output_dir = Path(output_dir)
        dest_path = output_dir / "artefacts" / "browser_history" / "History"

        candidate_paths = [
            "/data/data/com.android.chrome/app_chrome/Default/History",
            "/data/data/com.android.browser/databases/browser2.db",
            "/data/data/com.google.android.browser/databases/browser2.db"
        ]

        for device_path in candidate_paths:
            if self._device_file_exists(device_path):
                self.logger.info(f"Found browser history at {device_path}")
                result = self._pull_db_with_su_fallback(device_path, dest_path)
                if result:
                    return result

        self.logger.warn("No browser history database could be extracted.")
        return None

    def extract_whatsapp(self, output_dir):
        """
        Extract WhatsApp databases and keys if present.
        """
        self.logger.info("Extracting WhatsApp artefacts")
        output_dir = Path(output_dir)
        whatsapp_dir = output_dir / "artefacts" / "whatsapp"

        copied_paths = []

        candidate_files = [
            (
                "/data/data/com.whatsapp/databases/msgstore.db",
                whatsapp_dir / "msgstore.db"
            ),
            (
                "/data/data/com.whatsapp/files/key",
                whatsapp_dir / "key"
            )
        ]

        # Check internal storage media paths
        sdcard_dirs = [
            "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Databases",
            "/storage/emulated/0/WhatsApp/Databases"
        ]

        for device_path, dest_path in candidate_files:
            if self._device_file_exists(device_path):
                res = self._pull_db_with_su_fallback(device_path, dest_path)
                if res:
                    copied_paths.append(res)

        # Check databases in external storage
        for sdcard_dir in sdcard_dirs:
            try:
                # List databases in this dir
                res = self.device.shell(f"ls {sdcard_dir}")
                if "No such" not in res and "not found" not in res:
                    for line in res.splitlines():
                        line = line.strip()
                        if "msgstore.db" in line:
                            dev_file = f"{sdcard_dir}/{line}"
                            dst_file = whatsapp_dir / line
                            pull_res = self._pull_db_with_su_fallback(
                                dev_file, dst_file
                            )
                            if pull_res:
                                copied_paths.append(pull_res)
            except Exception:
                pass

        if not copied_paths:
            self.logger.warn("No WhatsApp artefacts were found or extracted.")

        return copied_paths

    def extract_media_metadata(
        self,
        output_dir
    ):
        """
        Extract /sdcard metadata with SHA-256 using on-device find & stat & sha256sum.
        """
        self.logger.info(
            "Extracting media metadata"
        )

        output_dir = Path(output_dir)

        metadata_output = (
            output_dir / "artefacts" / "media_metadata" / "media_metadata.json"
        )
        metadata_output.parent.mkdir(parents=True, exist_ok=True)

        cmd = (
            'find /storage/emulated/0 -path /storage/emulated/0/Android -prune '
            '-o -type f -exec sh -c \'for f; do stat -c "%n|%s|%Y" "$f" && '
            'sha256sum "$f"; done\' _ {} +'
        )

        result = self.device.shell(cmd)
        file_list = []
        lines = result.splitlines()

        i = 0
        while i < len(lines):
            stat_line = lines[i].strip()
            if not stat_line:
                i += 1
                continue

            if "|" in stat_line:
                parts = stat_line.split("|")
                if len(parts) >= 3:
                    path, size, mtime = parts[0], parts[1], parts[2]

                    sha256 = "UNKNOWN"
                    if i + 1 < len(lines):
                        sha_line = lines[i+1].strip()
                        if len(sha_line) >= 64:
                            sha256 = sha_line[:64]

                    file_list.append({
                        "path": path,
                        "size": int(size) if size.isdigit() else 0,
                        "modified": mtime,
                        "sha256": sha256
                    })
                    i += 2
                    continue
            i += 1

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