import os

from src.gnu_docs.config import DocsConfig
from src.utils import _download_file, _extract_archive, _load_versions


def download_and_extract(config: DocsConfig) -> None:
    """Download and extract Python documentation for all versions"""

    versions = _load_versions(str(config.versions_file))
    os.makedirs(config.downloads_path, exist_ok=True)
    os.makedirs(config.extracted_path, exist_ok=True)

    for version_info in versions.values():
        download_url = version_info["plain_text_link"]
        if not download_url:
            continue

        archive_name = os.path.basename(download_url)
        archive_path = os.path.join(config.downloads_path, archive_name)

        if _download_file(download_url, archive_path):
            print(f"Downloaded {version_info['specific']}")
            if _extract_archive(archive_path, str(config.extracted_path)):
                print(f"Extracted {version_info['specific']}")
