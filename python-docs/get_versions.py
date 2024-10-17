import os
import tarfile

import requests
import yaml
from constants import DOWNLOAD_DIR, EXTRACT_DIR, MAX_SKIP_COUNT, VERSIONS_FILE


def download_versions(versions_file: str, download_dir: str, max_skip_count: int):
    with open(versions_file, "r") as file:
        versions: dict = yaml.safe_load(file)["versions"]

    os.makedirs(download_dir, exist_ok=True)

    # Download versions or skip if max_skip_count is reached
    for _, details in versions.items():
        if details["skip"] >= max_skip_count:
            print(f"Skipping version {details['specific']}")
            continue

        url = details["plain_text_link"]
        if url:
            file_name = os.path.join(download_dir, os.path.basename(url))
            print(f"Downloading {url} to {file_name}...")

            try:
                response = requests.get(url)
                response.raise_for_status()

                with open(file_name, "wb") as file:
                    file.write(response.content)
                print(f"Downloaded successfully: {file_name}")

            except requests.RequestException as e:
                print(f"Failed to download {url}: {e}")


def extract_versions(extract_dir: str, download_dir: str):
    os.makedirs(extract_dir, exist_ok=True)

    # Extract downloaded versions
    for file_name in os.listdir(download_dir):
        if file_name.endswith(".tar.bz2"):
            file_path = os.path.join(download_dir, file_name)
            print(f"Extracting {file_path} to {extract_dir}...")

            try:
                with tarfile.open(file_path, "r:bz2") as tar:
                    tar.extractall(extract_dir, filter="data")
                print(f"Extraction complete for {file_name}")

            except tarfile.TarError as e:
                print(f"Failed to extract {file_name}: {e}")


if __name__ == "__main__":
    download_versions(VERSIONS_FILE, DOWNLOAD_DIR, MAX_SKIP_COUNT)
    extract_versions(EXTRACT_DIR, DOWNLOAD_DIR)
