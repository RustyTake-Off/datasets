from datetime import datetime
from typing import Any, Optional

import requests
import yaml
from bs4 import BeautifulSoup
from config import DocsConfig, VersionMetadata


def _parse_update_date(date_text: str) -> Optional[str]:
    """Extract and parse the update date from docs page text"""

    try:
        date_str = date_text.lower().replace("last updated", "").strip()
        return datetime.strptime(date_str, "%B %d, %Y").date().isoformat()
    except Exception as e:
        print(f"Failed to parse update date: {e}")
        return None


def _find_download_link(soup: BeautifulSoup, url: str) -> Optional[str]:
    """Find docs download link from the page"""

    try:
        for link in soup.find_all("a", href=True):
            href: str = link["href"]
            if ".info.tar.gz" in href:
                return url.format(version=href.split(".")[0]) + href
        return None

    except Exception as e:
        print(f"Failed to find download link: {e}")
        return None


def _extract_version_info(
    version: str,
    url: str,
    current_metadata: dict[str, Any],
):
    """Extract version information from docs page"""

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract last update date
        address_elements = soup.find_all("address")
        for address_element in address_elements:
            if "last updated" in address_element.text:
                update_element = address_element

                last_updated = (
                    _parse_update_date(update_element.text.strip())
                    if update_element
                    else None
                )

        # Extract download link
        download_url = _find_download_link(soup, url)

        return VersionMetadata(
            last_checked=datetime.now().date().isoformat(),
            last_update=last_updated or current_metadata["last_update"],
            download_url=download_url or current_metadata["plain_text_link"],
            specific_version=version or current_metadata["specific"],
        )

    except Exception as e:
        print(f"Error processing {version}: {e}")
        return _handle_version_error(current_metadata)


def _handle_version_error(metadata: dict[str, Any]) -> VersionMetadata:
    """Handle version processing error by incrementing retry count if below threshold"""

    return VersionMetadata(
        last_checked=datetime.now().date().isoformat(),
        last_update=metadata["last_update"],
        download_url=metadata["plain_text_link"],
        specific_version=metadata["specific"],
    )


def update_versions(config: DocsConfig) -> None:
    """Update version information for all versions"""

    with open(config.versions_file, "r") as file:
        data: dict = yaml.safe_load(file)

    updated_versions = {}
    unchanged_versions = {}
    for version, metadata in dict(data["versions"]).items():
        url = str(data["url"]).format(version=version)

        updated_info = _extract_version_info(version, url, metadata)
        updated_versions[version] = {
            "last_checked": updated_info.last_checked,
            "last_update": updated_info.last_update,
            "plain_text_link": updated_info.download_url,
            "specific": updated_info.specific_version,
        }

        print(f"Finished checking {version}")

    data["versions"] = {**unchanged_versions, **updated_versions}
    with open(config.versions_file, "w") as file:
        yaml.dump(data, file, default_flow_style=False)
