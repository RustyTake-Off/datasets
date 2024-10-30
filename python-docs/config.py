import os
from dataclasses import dataclass, field


@dataclass
class DocsConfig:
    """Configuration"""

    project_name: str = "python-docs"
    max_retry_attempts: int = 5
    update_threshold_days: int = 365
    section_separators: list[str] = field(default_factory=lambda: ["*", "=", "-"])

    def __post_init__(self):
        # Paths
        self.base_dir = os.path.join(os.getcwd(), self.project_name)
        self.downloads_path = os.path.join(self.base_dir, "downloads")
        self.extracted_path = os.path.join(self.base_dir, "extracted")
        self.output_path = os.path.join(self.base_dir, "data")
        self.versions_file = os.path.join(self.base_dir, "versions.yaml")

        if not os.path.exists(self.versions_file):
            raise ValueError(f"Versions file does not exists at: {self.versions_file}")


@dataclass
class VersionMetadata:
    """Metadata for versions"""

    last_checked: str
    last_update: str
    download_url: str
    specific_version: str
    retry_count: int = 0


@dataclass
class Section:
    """Metadata for sections"""

    title: str
    content: str
    source_file: str
