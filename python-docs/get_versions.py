import os
import tarfile

import requests
import yaml
from constants import DOWNLOAD_DIR, EXTRACT_DIR, MAX_SKIP_COUNT, VERSIONS_FILE

if __name__ == "__main__":
    # Load versions
    with open(VERSIONS_FILE, "r") as file:
        versions: dict = yaml.safe_load(file)["versions"]

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(EXTRACT_DIR, exist_ok=True)

    # Download versions or skip if MAX_SKIP_COUNT is reached
    for version, details in versions.items():
        if details["skip"] >= MAX_SKIP_COUNT:
            print(f"Skipping version {details['specific']}")
            continue

        url = details["plain_text_link"]
        if url:
            file_name = os.path.join(DOWNLOAD_DIR, os.path.basename(url))
            print(f"Downloading {url} to {file_name}...")

            try:
                response = requests.get(url)
                response.raise_for_status()

                with open(file_name, "wb") as file:
                    file.write(response.content)
                print(f"Downloaded successfully: {file_name}")

            except requests.RequestException as e:
                print(f"Failed to download {url}: {e}")

    # Extract downloaded versions
    for file_name in os.listdir(DOWNLOAD_DIR):
        if file_name.endswith(".tar.bz2"):
            file_path = os.path.join(DOWNLOAD_DIR, file_name)
            print(f"Extracting {file_path} to {EXTRACT_DIR}...")

            try:
                with tarfile.open(file_path, "r:bz2") as tar:
                    tar.extractall(EXTRACT_DIR, filter="data")
                print(f"Extraction complete for {file_name}")

            except tarfile.TarError as e:
                print(f"Failed to extract {file_name}: {e}")
