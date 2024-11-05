from datetime import datetime, timedelta
from typing import Any, Optional

import requests
import yaml
from bs4 import BeautifulSoup

from src.python_docs.config import DocsConfig, VersionMetadata
from src.utils import _parse_update_date


def _is_version_outdated(last_update: datetime, update_threshold_days: int) -> bool:
    """Check if version is older than update threshold"""

    return last_update < datetime.now() - timedelta(days=update_threshold_days)


def _extract_specific_version(soup: BeautifulSoup, version: str) -> Optional[str]:
    """Extract specific Python version from docs page title"""

    try:
        title_tag = soup.find("title")
        if not title_tag or not title_tag.text:
            return None

        title_words = title_tag.text.split()
        if version in title_tag.text:
            # Handle version format like 'v3.8.1' or '3.8.1'
            version_text = title_words[3]
            return version_text[1:] if version_text.startswith("v") else version_text

        return version  # Fallback to provided version if not found in title

    except Exception as e:
        print(f"Failed to extract specific version: {e}")
        return None


def _find_download_link(soup: BeautifulSoup, version: str) -> Optional[str]:
    """Find docs download link from the page"""

    try:
        for link in soup.find_all("a", href=True):
            href: str = link["href"]
            if "-docs-text.tar.bz2" in href:
                # Handle relative and absolute URLs
                if href.startswith("archives"):
                    return f"https://docs.python.org/{version}/{href}"
                return href
        return None

    except Exception as e:
        print(f"Failed to find download link: {e}")
        return None


def _extract_version_info(
    config: DocsConfig,
    version: str,
    url: str,
    current_metadata: dict[str, Any],
) -> VersionMetadata:
    """Extract version information from Python docs page"""

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract last update date
        p_element = soup.find("p")
        if p_element is not None:
            update_element = p_element.find_next("b")

        last_updated = (
            _parse_update_date(update_element.text.strip()) if update_element else None
        )

        if last_updated:
            if _is_version_outdated(
                datetime.fromisoformat(last_updated),
                config.update_threshold_days,
            ):
                return _handle_outdated_version(version, current_metadata)

        # Extract specific version and download link
        specific_version = _extract_specific_version(soup, version)
        download_url = _find_download_link(soup, version)

        return VersionMetadata(
            last_checked=datetime.now().date().isoformat(),
            last_update=last_updated or current_metadata["last_update"],
            download_url=download_url or current_metadata["plain_text_link"],
            specific_version=specific_version or current_metadata["specific"],
            retry_count=0,
        )

    except Exception as e:
        print(f"Error processing version {version}: {e}")
        return _handle_version_error(current_metadata, config.max_retry_attempts)


def _handle_outdated_version(version, metadata: dict[str, Any]) -> VersionMetadata:
    """Handle outdated version by incrementing retry count"""

    print(f"Skipping version {version}: outdated ({metadata["last_update"]})")

    return VersionMetadata(
        last_checked=datetime.now().date().isoformat(),
        last_update=metadata["last_update"],
        download_url=metadata["plain_text_link"],
        specific_version=metadata["specific"],
        retry_count=metadata["skip"] + 1,
    )


def _handle_version_error(
    metadata: dict[str, Any],
    max_retry_attempts,
) -> VersionMetadata:
    """Handle version processing error by incrementing retry count if below threshold"""

    new_retry_count = (
        metadata["skip"] + 1
        if metadata["skip"] < max_retry_attempts
        else metadata["skip"]
    )

    return VersionMetadata(
        last_checked=datetime.now().date().isoformat(),
        last_update=metadata["last_update"],
        download_url=metadata["plain_text_link"],
        specific_version=metadata["specific"],
        retry_count=new_retry_count,
    )


def update_versions(config: DocsConfig) -> None:
    """Update version information for all Python versions"""

    with open(config.versions_file, "r") as file:
        data: dict = yaml.safe_load(file)

    updated_versions = {}
    unchanged_versions = {}
    for version, metadata in dict(data["versions"]).items():
        major, minor = str(version).split(".")
        clean_version = f"{int(major)}.{int(minor)}"

        if metadata["skip"] >= config.max_retry_attempts:
            print(
                f"Skipping version {clean_version}: maximum retries reached ({config.max_retry_attempts})"
            )

            unchanged_versions[f"{int(major):02d}.{int(minor):02d}"] = {
                "last_checked": datetime.now().date().isoformat(),
                "last_update": metadata["last_update"],
                "plain_text_link": metadata["plain_text_link"],
                "specific": metadata["specific"],
                "skip": metadata["skip"],
            }
            continue

        url = str(data["url"]).format(version=clean_version)

        updated_info = _extract_version_info(config, clean_version, url, metadata)
        updated_versions[f"{int(major):02d}.{int(minor):02d}"] = {
            "last_checked": updated_info.last_checked,
            "last_update": updated_info.last_update,
            "plain_text_link": updated_info.download_url,
            "specific": updated_info.specific_version,
            "skip": updated_info.retry_count,
        }

        print(f"Finished checking {clean_version}")

    data["versions"] = {**unchanged_versions, **updated_versions}
    with open(config.versions_file, "w") as file:
        yaml.dump(data, file, default_flow_style=False)
