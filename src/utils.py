import os
import tarfile
from datetime import datetime
from typing import Optional

import requests
import yaml
from dotenv import load_dotenv


def _get_huggingface_token(provided_token: str | None = None) -> str:
    """
    Retrieves the HuggingFace token either from the provided argument or environment variables

    Args:
        provided_token (str | None): The token passed as an argument

    Returns:
        str: The HuggingFace token
    """

    if provided_token:
        return provided_token

    load_dotenv()
    token = os.getenv("HF_TOKEN")

    if token:
        print("Using token from environment variables")
        return token

    raise ValueError(
        "HuggingFace token is required either as an argument --token or an environment variable HF_TOKEN"
    )


def _load_versions(versions_file: str) -> dict:
    """Load version information from YAML file"""

    with open(versions_file, "r") as file:
        return yaml.safe_load(file)["versions"]


def _download_file(url: str, destination: str) -> bool:
    """Download file from URL to specified destination"""

    try:
        response = requests.get(url)
        response.raise_for_status()

        with open(destination, "wb") as file:
            file.write(response.content)
        return True

    except requests.RequestException as e:
        print(f"Download failed for {url}: {e}")
        return False


def _extract_archive(archive_path: str, extract_path: str) -> bool:
    """Extract downloaded archive to specified path"""

    try:
        if archive_path.endswith("bz2"):
            with tarfile.open(archive_path, "r:bz2") as tar:
                tar.extractall(extract_path, filter="data")
            return True
        else:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(extract_path, filter="data")
            return True

    except tarfile.TarError as e:
        print(f"Extraction failed for {archive_path}: {e}")
        return False


def _parse_update_date(date_text: str) -> Optional[str]:
    """Extract and parse the update date from docs page text in multiple formats"""

    try:
        # Check if the text contains "on: " format
        if "last updated on: " in date_text.lower():
            date_str = (
                date_text.lower().split("on: ")[1].split(" (")[0].strip().rstrip(".")
            )
            return datetime.strptime(date_str, "%b %d, %Y").date().isoformat()

        # Check if the text contains "Last updated" format
        elif "last updated" in date_text.lower():
            date_str = date_text.lower().replace("last updated", "").strip()
            return datetime.strptime(date_str, "%B %d, %Y").date().isoformat()

        # If neither format matches, return None
        else:
            print("Unrecognized date format.")
            return None

    except Exception as e:
        print(f"Failed to parse update date: {e}")
        return None
