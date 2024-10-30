import json
import os

from config import DocsConfig, Section


def _extract_sections(file_path: str, config: DocsConfig) -> list[Section]:
    """Extract documentation sections from a file"""

    sections = []
    current_title = None
    current_content = []

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

        for i in range(1, len(lines)):
            current_line = lines[i].strip()
            previous_line = lines[i - 1].strip()

            if _is_separator_line(current_line, config):
                if current_title:
                    sections.append(
                        Section(
                            title=current_title,
                            content="\n".join(current_content).strip(),
                            source_file=os.path.basename(file_path),
                        )
                    )
                current_title = previous_line
                current_content = []
            else:
                current_content.append(current_line)

        # Handle final section
        if current_title:
            sections.append(
                Section(
                    title=current_title,
                    content="\n".join(current_content).strip(),
                    source_file=os.path.basename(file_path),
                )
            )

    return sections


def _is_separator_line(line: str, config: DocsConfig) -> bool:
    """Check if line is a section separator"""

    return any(line.startswith(sep * 4) for sep in config.section_separators)


def _process_version_directory(
    version_dir: str,
    output_file: str,
    version_number: str,
    config: DocsConfig,
) -> None:
    """Process all files in a version directory and save sections to output file"""

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as out_file:
        for root, _, files in os.walk(version_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                sections = _extract_sections(file_path, config)

                for section in sections:
                    json.dump(
                        {
                            "section_title": section.title,
                            "section_content": section.content,
                            "file_name": section.source_file,
                        },
                        out_file,
                    )
                    out_file.write("\n")

        print(f"Successfully processed version {version_number}")


def process_documentation(config: DocsConfig) -> None:
    """Process all version directories and extract documentation sections"""

    for version_dir in os.listdir(config.extracted_path):
        version_path = os.path.join(config.extracted_path, version_dir)

        if os.path.isdir(version_path):
            version_number = version_dir.split("-")[1].split(".")
            major = int(version_number[0])
            minor = int(version_number[1])
            patch = int(version_number[2]) if len(version_number) > 2 else 0

            output_file = os.path.join(
                config.output_path, f"python-{major:02d}.{minor:02d}.{patch:02d}.jsonl"
            )
            _process_version_directory(
                version_path, output_file, f"{major}.{minor}", config
            )
