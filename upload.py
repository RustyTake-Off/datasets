import argparse
import os
from datetime import datetime

from huggingface_hub import HfApi


def upload_data_to_hf(
    search_term: str,
    repo_id: str,
    repo_type: str,
    token: str,
):
    """
    Upload data files from specified docs directory

    Args:
        search_term (str): Docs directory
        repo_id (str): Repository id e.g.: 'example-org/example-repo'
        repo_type (str): Repository type
        token (str): Hugging Face token
    """

    base = os.getcwd()
    search_term = f"{search_term}-docs"
    target_folder = os.path.join(base, search_term, "data")
    path_in_repo = f"data/{search_term}"

    if not os.path.exists(target_folder):
        print(f"Folder does not exist: {target_folder}")
        return

    client = HfApi(
        token=token,
    )

    # Upload entire 'data' folder
    client.upload_folder(
        commit_message=f"Upload {search_term} | {datetime.now().date()}",
        folder_path=target_folder,
        repo_id=repo_id,
        repo_type=repo_type,
        path_in_repo=path_in_repo,
    )

    client.upload_file(
        commit_message=f"Upload README.md | {datetime.now().date()}",
        path_in_repo="/README.md",
        path_or_fileobj="hf/README.md",
        repo_id=repo_id,
        repo_type=repo_type,
    )

    versions_file = os.path.join(base, search_term, "versions.yaml")
    if os.path.exists(versions_file):
        client.upload_file(
            commit_message=f"Upload versions.yaml | {datetime.now().date()}",
            path_in_repo=f"{path_in_repo}/versions.yaml",
            path_or_fileobj=versions_file,
            repo_id=repo_id,
            repo_type=repo_type,
        )


if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Upload documentation data to HuggingFace Hub",
    )
    parser.add_argument(
        "search_term",
        type=str,
        help="The term to search for",
    )
    parser.add_argument(
        "repo_id",
        type=str,
        help="Repository id e.g.: 'example-org/example-repo'",
    )
    parser.add_argument(
        "repo_type",
        type=str,
        help="Repository type",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Hugging Face token",
    )

    args = parser.parse_args()

    token = args.token or os.getenv("HF_TOKEN")
    if token is None:
        print(
            "HuggingFace token is required either as a argument --token or a environment variable HF_TOKEN"
        )

    upload_data_to_hf(
        search_term=args.search_term,
        repo_id=args.repo_id,
        repo_type=args.repo_type,
        token=str(token),
    )
