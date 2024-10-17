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

            # Check if the current line is a separator line with more than 3 symbols
            if any(line.startswith(separator * 4) for separator in separators):
                if current_title:
                    sections.append(
                        {
                            "section_title": current_title,
                            "section_content": "\n".join(current_content).strip(),
                            "file_name": os.path.basename(file_path),
                        }
                    )

                # Set new section title and reset content
                current_title = prev_line
                current_content = []
            else:
                current_content.append(line)

        # Handle last section in the file
        if current_title:
            sections.append(
                {
                    "section_title": current_title,
                    "section_content": "\n".join(current_content).strip(),
                    "file_name": os.path.basename(file_path),
                }
            )

    return sections


def process_files(extract_dir: str, output_dir: str, separators: list) -> None:
    """
    Process all version directories in the extract_dir and save extracted
    data to individual jsonl files in the output_dir for each version
    """

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for version_dir in os.listdir(extract_dir):
        version_path = os.path.join(extract_dir, version_dir)

        if os.path.isdir(version_path):
            # Extract version number
            version_specific = version_dir.split("-")[1]
            output_file = os.path.join(output_dir, f"py-{version_specific}.jsonl")

            with open(output_file, "w", encoding="utf-8") as file:
                for root, _, files in os.walk(version_path):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        sections = extract_sections(file_path, separators)

                        for section in sections:
                            file.write(json.dumps(section) + "\n")


if __name__ == "__main__":
    process_files(EXTRACT_DIR, OUTPUT_DIR, SEPARATORS)
