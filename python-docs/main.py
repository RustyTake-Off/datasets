from config import DocsConfig
from docs_downloader import download_and_extract
from docs_processor import process_documentation
from version_updater import update_versions


def main():
    """Main execution flow"""
    config = DocsConfig()

    # Update versions
    update_versions(config)

    # Download and extract docs
    download_and_extract(config)

    # Process docs files
    process_documentation(config)


if __name__ == "__main__":
    main()
