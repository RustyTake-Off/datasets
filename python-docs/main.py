import os
import tarfile

import requests
from constants import DOWNLOAD_DIR, EXTRACT_DIR, MAX_SKIP_COUNT, VERSIONS_FILE
from helpers import load_versions

# Create the download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


versions: dict[str, dict] = load_versions(VERSIONS_FILE)["versions"]

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
        os.makedirs(EXTRACT_DIR, exist_ok=True)

        try:
            with tarfile.open(file_path, "r:bz2") as tar:
                tar.extractall(EXTRACT_DIR, filter="data")
            print(f"Extraction complete for {file_name}")

        except tarfile.TarError as e:
            print(f"Failed to extract {file_name}: {e}")
