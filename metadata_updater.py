import argparse
import os
from datetime import datetime

from huggingface_hub import HfApi, list_repo_files, metadata_update
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError


def _generate_configs(repo_id: str, token: str) -> list:
    """Generate lang docs configurations from uploaded datasets on HuggingFace"""

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

    # Get all repo files
    versions = [
        version
        for version in list_repo_files(
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
        )
        if version.endswith(".jsonl")
    ]

    configs = []
    for version in versions:
        # Get version info
        lang, version = version.replace(".jsonl", "").split("/")[-1].split("-")

        # Clean up version format
        version_split = [str(int(part)) for part in version.split(".")]
        cleaned_version = ".".join(version_split)

        # Create config entry
        config_entry = {
            "config_name": f"{lang}-{cleaned_version}",
            "data_files": [
                {
                    "split": "train",
                    "path": f"data/{lang}-docs/*-{version}.*",
                }
            ],
        }
        configs.append(config_entry)

    # Add general config for the language
    general_config = {
        "config_name": f"{lang}",
        "data_files": [
            {
                "split": "train",
                "path": f"data/{lang}-docs",
            }
        ],
    }
    configs.append(general_config)

    configs.sort(key=lambda x: x["data_files"][0]["path"])

    return configs


def _upload_metadata_to_hf(repo_id: str, token: str) -> None:
    """Upload lang docs configurations to HuggingFace"""

    # Generate configs
    generated_configs = _generate_configs(repo_id, token)

    generated_configs.sort(key=lambda x: x["data_files"][0]["path"])
    configs_dict = {"configs": generated_configs}

    # Upload metadata to HuggingFace
    metadata_update(
        commit_message=f"Update readme | {datetime.now().date()}",
        commit_description="Update readme with lang docs config names",
        metadata=configs_dict,
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
        "--repo_id",
        type=str,
        default="RustyTake-Off/misc",
        help="HuggingFace repository id (e.g. 'example-org/example-repo')",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="HuggingFace token with user write access to repositories and prs",
    )
    args = parser.parse_args()

    # Handle token retrieval
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

    _upload_metadata_to_hf(
        repo_id=args.repo_id,
        token=token,
    )


if __name__ == "__main__":
    metadata_updater()
