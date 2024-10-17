import json
import os

from constants import EXTRACT_DIR, OUTPUT_DIR, SEPARATORS


def extract_sections(file_path: str, separators: list) -> list:
    """
    Extract sections

    Args:
        file_path (str): File to extract sections from

    Returns:
        list: Sections
    """

    sections = []
    current_title = None
    current_content = []

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

        for i in range(1, len(lines)):
            line = lines[i].strip()
            prev_line = lines[i - 1].strip()

            # Check if the current line is a separator line (more than 3 symbols)
            if any(line.startswith(separator * 4) for separator in separators):
                if current_title:  # If there's an existing title, store the section
                    sections.append(
                        {
                            "section_title": current_title,
                            "section_content": "\n".join(current_content).strip(),
                            "file_name": os.path.basename(file_path),
                        }
                    )

                # Set the new section title and reset content
                current_title = prev_line
                current_content = []
            else:
                current_content.append(line)

        # Handle the last section in the file
        if current_title:
            sections.append(
                {
                    "section_title": current_title,
                    "section_content": "\n".join(current_content).strip(),
                    "file_name": os.path.basename(file_path),
                }
            )

    return sections


def process_files() -> None:
    """
    Process all version directories in the EXTRACT_DIR and save the extracted
    data to individual JSONL files in the OUTPUT_DIR for each version
    """
    for version_dir in os.listdir(EXTRACT_DIR):
        version_path = os.path.join(EXTRACT_DIR, version_dir)
        if os.path.isdir(version_path):
            # Extract the version number
            version_specific = version_dir.split("-")[1]
            output_file = os.path.join(OUTPUT_DIR, f"py-{version_specific}.jsonl")

            with open(output_file, "w", encoding="utf-8") as file:
                for root, _, files in os.walk(version_path):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        sections = extract_sections(file_path, SEPARATORS)
                        for section in sections:
                            file.write(json.dumps(section) + "\n")


if __name__ == "__main__":
    process_files()
