from datetime import datetime, timedelta
from typing import Any, Optional

import requests
import yaml
from bs4 import BeautifulSoup

# Load the YAML file
versions_file = "versions.yaml"


# Constants
ONE_YEAR_DAYS = 365
MAX_SKIP_COUNT = 6


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


def extract_python_doc_info(
    version: str,
    url: str,
    details: dict[str, Any],
) -> dict[str, str]:
    """
    Fetches and extracts Python documentation details for a given version

    Args:
        version (str): Python version (e.g., "3.9")
        url (str): URL of the documentation page
        details (dict[str, Any]): Metadata about the version
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the last update date
        p_tag = soup.find("p")

        if p_tag is not None:
            b_tag = p_tag.find_next("b")

            if b_tag is not None and b_tag.text:
                last_updated = b_tag.text.strip()

        if last_updated:
            last_updated = cleanup_date(last_updated)
            last_update_date = datetime.fromisoformat(last_updated)
            one_year_ago = datetime.now() - timedelta(days=ONE_YEAR_DAYS)

            if last_update_date < one_year_ago:
                details["skip"] += 1
                print(
                    f"Version {version} last updated on {last_updated}, skipping. Current counter {details['skip']}"
                )

                if details["skip"] >= MAX_SKIP_COUNT:
                    details["skip"] = True
                    print(f"Skipping version {version} after {MAX_SKIP_COUNT} counts")

                return {
                    "last_update": details["last_update"],
                    "plain_text_link": details["plain_text_link"],
                    "specific": details["specific"],
                }

        # Extract the specific Python version from the title
        title_tag = soup.find("title")
        title = title_tag.text if title_tag else ""

        if version in title:
            specific_version = (
                title.split()[3][1:]
                if title.split()[3].startswith("v")
                else title.split()[3]
            )
        else:
            specific_version = version

        # Find the plain text download link
        links = soup.find_all("a", href=True)
        for link in links:
            if "-docs-text.tar.bz2" in link["href"]:
                plain_text_link: str = link["href"]

                if plain_text_link.startswith("archives"):
                    plain_text_link = (
                        f"https://docs.python.org/{version}/{plain_text_link}"
                    )
                break

        details["skip"] = 0
        print(
            f"Done checking version {version}, resetting counter to {details['skip']}"
        )

        return {
            "last_update": last_updated,
            "plain_text_link": plain_text_link,
            "specific": specific_version,
        }

    except Exception as e:
        print(f"Error processing version {version}: {str(e)}")
        # Increment the skip counter if it's not already True
        if details["skip"] is not True:
            details["skip"] += 1

        # Check if the skip counter reaches MAX_SKIP_COUNT
        if details["skip"] >= MAX_SKIP_COUNT:
            details["skip"] = True
            print(f"Skipping version {version} after {MAX_SKIP_COUNT} counts")

        return {
            "last_update": details["last_update"],
            "plain_text_link": details["plain_text_link"],
            "specific": details["specific"],
        }


# Load the versions data from the YAML file
data = load_versions(versions_file)

for version, details in data["versions"].items():
    # Remove leading zeros from the version to construct the URL
    major, minor = version.split(".")
    clean_version = f"{int(major)}.{int(minor)}"

    # Skip the version if skip is true
    if details["skip"] is True:
        print(f"Skipping version {clean_version}")
        continue

    url = data["url"].format(version=clean_version)
    info = extract_python_doc_info(clean_version, url, details)

    # Update the YAML data with the extracted information
    details["last_update"] = info["last_update"]
    details["plain_text_link"] = info["plain_text_link"]
    details["specific"] = info["specific"]

# Write the updated data back to the YAML file
update_versions(versions_file, data)
