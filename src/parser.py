"""
parser.py

Parsers for Android dumpsys output and other command line results.
"""

import re


class DumpsysPackageParser:
    """
    Parses 'dumpsys package' output to extract package metadata.
    """

    def parse(self, dump_output):
        """
        Parses dumpsys package output string.
        Returns a dictionary mapping package names to metadata dicts.
        """
        packages = {}
        current_package = None

        package_re = re.compile(r'^\s*Package\s*\[([^\]]+)\]')
        version_re = re.compile(r'^\s*versionName=(.*)$')
        first_install_re = re.compile(r'^\s*firstInstallTime=(.*)$')
        last_update_re = re.compile(r'^\s*lastUpdateTime=(.*)$')

        for line in dump_output.splitlines():
            pkg_match = package_re.match(line)
            if pkg_match:
                current_package = pkg_match.group(1)
                packages[current_package] = {
                    "versionName": "UNKNOWN",
                    "firstInstallTime": "UNKNOWN",
                    "lastUpdateTime": "UNKNOWN"
                }
                continue

            if current_package:
                v_match = version_re.match(line)
                if v_match:
                    packages[current_package]["versionName"] = v_match.group(1).strip()
                    continue

                fi_match = first_install_re.match(line)
                if fi_match:
                    packages[current_package]["firstInstallTime"] = fi_match.group(1).strip()
                    continue

                lu_match = last_update_re.match(line)
                if lu_match:
                    packages[current_package]["lastUpdateTime"] = lu_match.group(1).strip()
                    continue

        return packages
