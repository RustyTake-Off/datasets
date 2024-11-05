import os
import tarfile

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
