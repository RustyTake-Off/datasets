import argparse
import os
from datetime import datetime
from itertools import chain

from huggingface_hub import HfApi, dataset_info, metadata_update
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError


def _generate_configs() -> list:
    """Generate dataset configurations from the versions in the specified directory"""

    lang_docs = []
    for doc in os.listdir(os.path.curdir):
        if "-docs" in doc:
            lang_docs.append(doc)

    configs = []
    for lang in lang_docs:
        data_dir = os.path.join(lang, "data")
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"'{data_dir}' does not exist")

        versions = os.listdir(data_dir)

        for version in versions:
            # Get version info
            lang, version = version.replace(".jsonl", "").split("-")

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

    return configs


def _save_and_update_metadata(
    repo_id: str,
    token: str,
    hf_directory: str = "hf",
) -> None:
    """
    Save and update metadata on HuggingFace

    Args:
        hf_directory (str): Directory for HuggingFace files (e.g., 'hf')
        repo_id (str): HuggingFace repository id (e.g. 'example-org/example-repo')
        token (str): HuggingFace token with user write access to repositories and prs
    """

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

    # Generate configs
    generated_configs = _generate_configs()

    # Load configs from HuggingFace
    current_configs = dataset_info(
        repo_id=repo_id,
        token=token,
    ).cardData.to_dict()

    if "configs" not in current_configs:
        current_configs["configs"] = []

    new_configs = list(
        {
            item["config_name"]: item
            for item in chain(generated_configs, current_configs["configs"])
        }.values()
    )
    new_configs.sort(key=lambda x: x["data_files"][0]["path"])

    # Save the config to a local markdown file
    # from huggingface_hub import metadata_save

    # local_path = os.path.join(hf_directory, "lang-docs-config-names.md")
    # metadata_save(local_path=local_path, data=config_dict)

    # Update metadata on HuggingFace
    metadata_update(
        commit_message=f"Update readme | {datetime.now().date()}",
        commit_description="Update readme with lang docs config names",
        metadata={"configs": new_configs},
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
        "--hf_directory",
        type=str,
        default="hf",
        help="Directory for HuggingFace files (e.g., 'hf')",
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

    # Run the save and update process
    _save_and_update_metadata(
        repo_id=args.repo_id,
        hf_directory=args.hf_directory,
        token=str(token),
    )


if __name__ == "__main__":
    metadata_updater()
