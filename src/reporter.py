"""
reporter.py

HTML report generation.
"""

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class ReportGenerator:
    """
    Generates HTML reports.
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

    def generate(
        self,
        output_dir,
        case_id,
        investigator
    ):

        output_dir = Path(
            output_dir
        )

        template = self.env.get_template(
            "report.html.j2"
        )

        device_info = json.load(
            open(
                output_dir /
                "device_info.json"
            )
        )

        manifest = json.load(
            open(
                output_dir /
                "manifest.json"
            )
        )

        apps = json.load(
            open(
                output_dir /
                "installed_apps.json"
            )
        )

        media = json.load(
            open(
                output_dir /
                "media_metadata.json"
            )
        )

        html = template.render(
            case_id=case_id,
            investigator=investigator,
            device=device_info,
            manifest=manifest,
            app_count=len(apps),
            media_count=len(media)
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
            file.write(
                html
            )

        return report_path