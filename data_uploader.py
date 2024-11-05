import argparse
import glob
import os
from datetime import datetime

from huggingface_hub import CommitOperationAdd, HfApi
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError

from utils import _get_huggingface_token


def _upload_data_to_hf(lang: str, repo_id: str, token: str) -> None:
    """
    Upload data files from specified docs directory

    Args:
        lang (str): Docs directory containing dataset files (e.g. 'python', 'javascript')
        repo_id (str): HuggingFace repository id (e.g. 'example-org/example-repo')
        token (str): HuggingFace token with user write access to repositories and PRs
    """

    base = os.curdir
    lang = f"{lang}-docs"
    target_folder = os.path.join(base, lang, "data")
    path_in_repo = f"data/{lang}"

    if not os.path.exists(target_folder):
        raise FileNotFoundError(f"'{target_folder}' does not exist")

    client = HfApi(token=token)
    try:
        client.auth_check(repo_id=repo_id, repo_type="dataset", token=token)
    except (GatedRepoError, RepositoryNotFoundError) as e:
        print(f"Repository access error: {e}")
        return

    # Collect files for commit
    operations = [
        CommitOperationAdd(
            path_in_repo=f"{path_in_repo}/{os.path.relpath(file_path, target_folder)}",
            path_or_fileobj=file_path,
        )
        for file_path in glob.glob(os.path.join(target_folder, "**"), recursive=True)
        if os.path.isfile(file_path)
    ]

    # Add versions.yaml if it exists
    versions_file = os.path.join(base, lang, "versions.yaml")
    if os.path.exists(versions_file):
        operations.append(
            CommitOperationAdd(
                path_in_repo=f"{path_in_repo}/versions.yaml",
                path_or_fileobj=versions_file,
            )
        )

    # Commit to HuggingFace
    client.create_commit(
        commit_message=f"Update {lang} | {datetime.now().date()}",
        operations=operations,
        repo_id=repo_id,
        repo_type="dataset",
        token=token,
        create_pr=True,
    )


def data_uploader() -> None:
    parser = argparse.ArgumentParser(
        description="Upload docs data to HuggingFace Hub",
    )
    parser.add_argument(
        "lang",
        type=str,
        help="Docs directory containing dataset files (e.g., 'python', 'javascript')",
    )
    parser.add_argument(
        "repo_id",
        type=str,
        help="HuggingFace repository id (e.g. 'example-org/example-repo')",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="HuggingFace token with user write access to repositories and prs",
    )
    args = parser.parse_args()

    # Handle token retrieval
    token = _get_huggingface_token(args.token)
    _upload_data_to_hf(
        lang=args.lang,
        repo_id=args.repo_id,
        token=token,
    )


if __name__ == "__main__":
    data_uploader()
