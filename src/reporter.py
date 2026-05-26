"""
reporter.py

HTML and JSON report generation.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


def format_timestamp(ts):
    """
    Convert Android millisecond/second timestamps to human-readable strings.
    """
    try:
        if not ts:
            return "N/A"
        val = int(ts)
        # If timestamp is in microseconds (16 digits or more)
        if val > 9999999999999:
            return datetime.fromtimestamp(val / 1000000).strftime('%Y-%m-%d %H:%M:%S')
        # If timestamp is in milliseconds (13 digits)
        if val > 9999999999:
            return datetime.fromtimestamp(val / 1000).strftime('%Y-%m-%d %H:%M:%S')
        # Standard Unix timestamp
        return datetime.fromtimestamp(val).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(ts)


class ReportGenerator:
    """
    Generates forensic HTML and JSON reports.
    """

    def __init__(
        self,
        template_dir
    ):
        self.env = Environment(
            loader=FileSystemLoader(
                template_dir
            )
        )
        self.env.filters['format_ts'] = format_timestamp

    def get_sqlite_row_count(self, db_path, table_name):
        """
        Helper to count rows in a specific SQLite table.
        """
        if not Path(db_path).exists():
            return 0
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def get_call_logs(self, db_path):
        """
        Extract recent call logs from contacts2.db.
        """
        if not Path(db_path).exists():
            return []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT number, date, duration, type FROM calls "
                "ORDER BY date DESC LIMIT 100"
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception:
            return []

    def get_sms_logs(self, db_path):
        """
        Extract recent SMS messages from mmssms.db.
        """
        if not Path(db_path).exists():
            return []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT address, date, body, type FROM sms "
                "ORDER BY date DESC LIMIT 100"
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception:
            return []

    def get_browser_history(self, db_path):
        """
        Extract recent browser history from Chrome History DB.
        """
        if not Path(db_path).exists():
            return []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Chrome History uses WebKit/Chrome epoch (Jan 1, 1601 UTC in microseconds)
            # but we can query raw columns and convert last_visit_time.
            cursor.execute(
                "SELECT url, title, visit_count, last_visit_time FROM urls "
                "ORDER BY last_visit_time DESC LIMIT 100"
            )
            rows = []
            for r in cursor.fetchall():
                d = dict(r)
                # Convert Chrome microsecond timestamp (since 1601) to Unix
                # 11644473600000000 is the difference in microseconds between 1601 and 1970
                try:
                    chrome_ts = int(d['last_visit_time'])
                    if chrome_ts > 0:
                        unix_ts = (chrome_ts - 11644473600000000) / 1000000
                        d['last_visit_time'] = unix_ts
                except Exception:
                    pass
                rows.append(d)
            conn.close()
            return rows
        except Exception:
            return []

    def generate_json_report(
        self,
        output_dir,
        case_id,
        investigator,
        manifest,
        app_count,
        media_count,
        call_log_count,
        sms_count,
        browser_count,
        whatsapp_count
    ):
        """
        Generate machine-readable JSON report.
        """
        output_dir = Path(output_dir)
        device_info_path = output_dir / "device_info.json"
        device_info = {}
        if device_info_path.exists():
            with open(device_info_path, "r", encoding="utf-8") as f:
                device_info = json.load(f)

        report_data = {
            "case_id": case_id,
            "investigator": investigator,
            "timestamp": datetime.now().isoformat(),
            "device_info": device_info,
            "summary": {
                "installed_apps_count": app_count,
                "media_files_count": media_count,
                "call_log_count": call_log_count,
                "sms_count": sms_count,
                "browser_history_count": browser_count,
                "whatsapp_files_count": whatsapp_count
            },
            "manifest": manifest
        }

        report_json_path = output_dir / "report.json"
        with open(report_json_path, "w", encoding="utf-8") as file:
            json.dump(report_data, file, indent=4)

        return report_json_path

    def generate(
        self,
        output_dir,
        case_id,
        investigator,
        manifest=None
    ):
        """
        Generate HTML report.
        """
        output_dir = Path(output_dir)

        template = self.env.get_template(
            "report.html.j2"
        )

        device_info_path = output_dir / "device_info.json"
        device_info = {}
        if device_info_path.exists():
            device_info = json.load(open(device_info_path, encoding="utf-8"))

        if manifest is None:
            manifest_path = output_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.load(open(manifest_path, encoding="utf-8"))
            else:
                manifest = {}

        apps_path = output_dir / "installed_apps.json"
        apps = []
        if apps_path.exists():
            apps = json.load(open(apps_path, encoding="utf-8"))

        media_path = (
            output_dir / "artefacts" / "media_metadata" / "media_metadata.json"
        )
        media = []
        if media_path.exists():
            media = json.load(open(media_path, encoding="utf-8"))

        # Load DB counts and contents
        call_log_db = output_dir / "artefacts" / "call_log" / "contacts2.db"
        call_log_count = self.get_sqlite_row_count(call_log_db, "calls")
        call_logs = self.get_call_logs(call_log_db)

        sms_db = output_dir / "artefacts" / "sms" / "mmssms.db"
        sms_count = self.get_sqlite_row_count(sms_db, "sms")
        sms_logs = self.get_sms_logs(sms_db)

        browser_db = output_dir / "artefacts" / "browser_history" / "History"
        browser_count = self.get_sqlite_row_count(browser_db, "urls")
        browser_logs = self.get_browser_history(browser_db)

        # Count whatsapp files
        whatsapp_dir = output_dir / "artefacts" / "whatsapp"
        whatsapp_files = []
        if whatsapp_dir.exists():
            whatsapp_files = [
                f.name for f in whatsapp_dir.iterdir() if f.is_file()
            ]

        # Generate JSON report first
        self.generate_json_report(
            output_dir=output_dir,
            case_id=case_id,
            investigator=investigator,
            manifest=manifest,
            app_count=len(apps),
            media_count=len(media),
            call_log_count=call_log_count,
            sms_count=sms_count,
            browser_count=browser_count,
            whatsapp_count=len(whatsapp_files)
        )

        # Render HTML report
        html = template.render(
            case_id=case_id,
            investigator=investigator,
            device=device_info,
            manifest=manifest,
            apps=apps,
            app_count=len(apps),
            media=media,
            media_count=len(media),
            call_log_count=call_log_count,
            call_logs=call_logs,
            sms_count=sms_count,
            sms_logs=sms_logs,
            browser_count=browser_count,
            browser_logs=browser_logs,
            whatsapp_count=len(whatsapp_files),
            whatsapp_files=whatsapp_files,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        report_path = (
            output_dir /
            "report.html"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(html)

        return report_path