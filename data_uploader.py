import argparse
import glob
import os
from datetime import datetime

from huggingface_hub import CommitOperationAdd, HfApi
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError


def _upload_data_to_hf(
    lang: str,
    repo_id: str,
    token: str,
) -> None:
    """
    Upload data files from specified docs directory

    Args:
        lang (str): Docs directory containing dataset files (e.g. 'python', 'javascript')
        repo_id (str): HuggingFace repository id (e.g. 'example-org/example-repo')
        token (str): HuggingFace token with user write access to repositories and prs
    """

    base = os.curdir
    lang = f"{lang}-docs"
    target_folder = os.path.join(base, lang, "data")
    path_in_repo = f"data/{lang}"

    if not os.path.exists(target_folder):
        raise FileNotFoundError(f"'{target_folder}' does not exist")

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

    versions_file = os.path.join(base, lang, "versions.yaml")
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

    _upload_data_to_hf(
        lang=args.lang,
        repo_id=args.repo_id,
        token=str(token),
    )


if __name__ == "__main__":
    data_uploader()
