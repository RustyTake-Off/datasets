import os
import tarfile

import requests
import yaml
from config import DocsConfig


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
        with tarfile.open(archive_path, "r:bz2") as tar:
            tar.extractall(extract_path, filter="data")
        return True

    except tarfile.TarError as e:
        print(f"Extraction failed for {archive_path}: {e}")
        return False


def download_and_extract(config: DocsConfig) -> None:
    """Download and extract Python documentation for all versions"""

    versions = _load_versions(str(config.versions_file))
    os.makedirs(config.downloads_path, exist_ok=True)
    os.makedirs(config.extracted_path, exist_ok=True)

    for version_info in versions.values():
        if version_info["skip"] >= config.max_retry_attempts:
            print(
                f"Skipping version {version_info['specific']}: maximum retries reached"
            )
            continue

        download_url = version_info["plain_text_link"]
        if not download_url:
            continue

        archive_name = os.path.basename(download_url)
        archive_path = os.path.join(config.downloads_path, archive_name)

        if _download_file(download_url, archive_path):
            print(f"Downloaded version {version_info['specific']}")
            if _extract_archive(archive_path, str(config.extracted_path)):
                print(f"Extracted version {version_info['specific']}")
