import argparse
import glob
import os
from datetime import datetime

from huggingface_hub import CommitOperationAdd, HfApi
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError


def upload_data_to_hf(
    search_term: str,
    repo_id: str,
    token: str,
):
    """
    Upload data files from specified docs directory

    Args:
        search_term (str): Docs directory e.g.: 'python', 'javascript'
        repo_id (str): Repository id e.g.: 'example-org/example-repo'
        token (str): Hugging Face token with user write access to repositories and prs
    """

    base = os.curdir
    search_term = f"{search_term}-docs"
    target_folder = os.path.join(base, search_term, "data")
    path_in_repo = f"data/{search_term}"

    if not os.path.exists(target_folder):
        raise FileNotFoundError(f"Folder does not exist: {target_folder}")

    try:
        client = HfApi(token=token)
        client.auth_check(
            repo_id=repo_id,
            repo_type="dataset",
            token=client.token,
        )
    except GatedRepoError:
        print("You do not have permission to access this gated repository")
    except RepositoryNotFoundError:
        print("The repository was not found or you do not have access")

    operations = []
    for file_path in glob.glob(os.path.join(target_folder, "**"), recursive=True):
        if os.path.isfile(file_path):
            relative_path = os.path.relpath(file_path, target_folder)
            operations.append(
                CommitOperationAdd(
                    path_in_repo=f"{path_in_repo}/{relative_path}",
                    path_or_fileobj=file_path,
                )
            )

    versions_file = os.path.join(base, search_term, "versions.yaml")
    if os.path.exists(versions_file):
        operations.append(
            CommitOperationAdd(
                path_in_repo=f"{path_in_repo}/versions.yaml",
                path_or_fileobj=versions_file,
            )
        )

    readme_file = os.path.join(base, "hf", "README.md")
    if os.path.exists(versions_file):
        operations.append(
            CommitOperationAdd(
                path_in_repo="/README.md",
                path_or_fileobj=readme_file,
            )
        )

    client.create_commit(
        commit_message=f"Update {search_term} | {datetime.now().date()}",
        operations=operations,
        repo_id=repo_id,
        repo_type="dataset",
        token=token,
        create_pr=True,
    )


if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Upload docs data to HuggingFace Hub",
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
        "--token",
        type=str,
        help="Hugging Face token",
    )
    args = parser.parse_args()

    token = args.token
    if token is None or token == "":
        from dotenv import load_dotenv

        load_dotenv()
        token = os.getenv("HF_TOKEN")

        if token:
            print("Using token from environment variables")
        else:
            raise ValueError(
                "HuggingFace token is required either as an argument --token or an environment variable HF_TOKEN"
            )

    upload_data_to_hf(
        search_term=args.search_term,
        repo_id=args.repo_id,
        token=str(token),
    )
