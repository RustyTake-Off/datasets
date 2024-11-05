from src.gnu_docs.config import DocsConfig
from src.gnu_docs.docs_downloader import download_and_extract
from src.gnu_docs.docs_processor import process_documentation
from src.gnu_docs.version_updater import update_versions


def main():
    """Main execution flow"""
    config = DocsConfig()

    # Update versions
    update_versions(config)

    # Download and extract docs
    download_and_extract(config)

    # Process docs files
    process_documentation(config)
