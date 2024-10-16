from datetime import datetime
from typing import Any

import yaml


def load_versions(versions_file: str) -> dict[str, Any]:
    """Load the version data from a YAML file"""

    with open(versions_file, "r") as file:
        return yaml.safe_load(file)


def update_versions(versions_file: str, data: dict[str, Any]) -> None:
    """Update the YAML file with formatted version numbers"""

    formatted_versions = {
        f"{int(major):02d}.{int(minor):02d}": details
        for version, details in data["versions"].items()
        for major, minor in [version.split(".")]
    }

    data["versions"] = formatted_versions

    with open(versions_file, "w") as file:
        yaml.dump(data, file, default_flow_style=False)


def cleanup_date(last_updated: str) -> str:
    """Clean the last updated date string and return ISO format"""

    try:
        date_str = last_updated.split("on: ")[1].split(" (")[0].strip().rstrip(".")
        return datetime.strptime(date_str, "%b %d, %Y").date().isoformat()
    except Exception as e:
        print(f"Error cleaning last update date: {str(e)}")
        return last_updated
