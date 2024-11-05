import argparse
from datetime import datetime

from huggingface_hub import HfApi, list_repo_files, metadata_update
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError

from utils import _get_huggingface_token


def _generate_configs(repo_id: str, token: str) -> list:
    """Generate lang docs configurations from uploaded datasets on HuggingFace"""

    client = HfApi(token=token)
    try:
        client.auth_check(repo_id=repo_id, repo_type="dataset", token=token)
    except (GatedRepoError, RepositoryNotFoundError) as e:
        print(f"Repository access error: {e}")
        return []

    # Get files from repo
    versions = [
        version
        for version in list_repo_files(
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
        )
        if version.endswith(".jsonl")
    ]

    # Create specific config entries
    configs = []
    for version in versions:
        # Parse language and version
        version = version.replace(".jsonl", "")
        lang_docs = version.split("/")[-1].split("-")[0]
        lang = version.split("/")[1].split("-")[0]
        version = version.split("/")[-1].split("-")[1]

        # Clean up version format
        cleaned_version = ".".join([str(int(part)) for part in version.split(".")])

        # Config entry for each version
        configs.append(
            {
                "config_name": f"{lang_docs}-{cleaned_version}",
                "data_files": [
                    {
                        "split": "train",
                        "path": f"data/{lang}-docs/{lang_docs}-{version}.*",
                    }
                ],
            }
        )

    # Add general config entry for each unique language
    unique_langs = set(version.split("/")[1].split("-")[0] for version in versions)
    for lang_docs in unique_langs:
        configs.append(
            {
                "config_name": f"{lang_docs}",
                "data_files": [
                    {
                        "split": "train",
                        "path": f"data/{lang_docs}-docs",
                    }
                ],
            }
        )

    return sorted(configs, key=lambda x: x["data_files"][0]["path"])


def _upload_metadata_to_hf(repo_id: str, token: str) -> None:
    """Upload lang docs configurations to HuggingFace"""

    configs = _generate_configs(repo_id, token)
    if not configs:
        print("No configs generated")
        return

    # Upload metadata to HuggingFace
    metadata_update(
        commit_message=f"Update readme | {datetime.now().date()}",
        commit_description="Update readme with lang docs config names",
        metadata={"configs": configs},
        repo_id=repo_id,
        repo_type="dataset",
        token=token,
        overwrite=True,
        create_pr=True,
    )


def metadata_updater() -> None:
    parser = argparse.ArgumentParser(
        description="Generate and update HuggingFace metadata for dataset configs",
    )
    parser.add_argument(
        "repo_id",
        type=str,
        help="HuggingFace repository id (e.g. 'example-org/example-repo')",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="HuggingFace token with user write access to repositories and PRs",
    )
    args = parser.parse_args()

    # Handle token retrieval
    token = _get_huggingface_token(args.token)
    _upload_metadata_to_hf(
        repo_id=args.repo_id,
        token=token,
    )


if __name__ == "__main__":
    metadata_updater()
