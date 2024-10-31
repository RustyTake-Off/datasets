import argparse
import os
from datetime import datetime

from huggingface_hub import HfApi, metadata_load, metadata_save, metadata_update
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError


def _generate_configs(lang: str) -> list:
    """Generate dataset configurations from the versions in the specified directory"""

    configs = []
    data_dir = os.path.join(f"{lang}-docs", "data")
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

    configs.sort(key=lambda x: x["data_files"][0]["path"])

    return configs


def _generate_and_save_metadata(
    lang: str,
    repo_id: str,
    token: str,
    hf_dir: str,
) -> None:
    """
    Save and update metadata on HuggingFace

    Args:
        lang (str): Lang docs data to generate config names from (e.g. 'python', 'java')
        repo_id (str): HuggingFace repository id (e.g. 'example-org/example-repo')
        token (str): HuggingFace token with user write access to repositories and prs
        hf_dir (str): Directory for HuggingFace files (e.g., 'hf')
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
    generated_configs = _generate_configs(lang)
    new_configs_dict = {"configs": generated_configs}

    # Save the config to a local markdown file
    local_path = os.path.join(hf_dir, f"{lang}-config-names.md")
    os.makedirs(hf_dir, exist_ok=True)
    if os.path.exists(hf_dir):
        metadata_save(local_path=local_path, data=new_configs_dict)


def _upload_metadata_to_hf(repo_id: str, token: str, hf_dir: str) -> None:
    """Load lang docs config names and upload the to HuggingFace"""

    hf_path = os.path.join(os.path.curdir, hf_dir)
    os.makedirs(hf_path, exist_ok=True)

    lang_configs_paths = []
    for doc in os.listdir(hf_path):
        if "-config-names" in doc:
            lang_configs_paths.append(os.path.join(hf_path, doc))

    if lang_configs_paths == []:
        print(
            f"Could not find any lang docs config names in '{hf_dir}' to upload to HuggingFace repo"
        )
        return

    configs = []
    for path in lang_configs_paths:
        config_names = metadata_load(path)

        if config_names and "configs" in config_names:
            configs.extend(config_names["configs"])

    configs.sort(key=lambda x: x["data_files"][0]["path"])
    configs_dict = {"configs": configs}

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
        "--lang",
        type=str,
        help="Lang docs data to generate config names from (e.g. 'python', 'java')",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="HuggingFace token with user write access to repositories and prs",
    )
    parser.add_argument(
        "--hf_dir",
        type=str,
        default="hf",
        help="Directory for HuggingFace files (e.g., 'hf')",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Include this flag to upload metadata to the HuggingFace repo",
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

    hf_dir = f"{args.hf_dir}-docs"

    if args.lang:
        _generate_and_save_metadata(
            lang=args.lang,
            repo_id=args.repo_id,
            token=str(token),
            hf_dir=hf_dir,
        )
    else:
        print("Skipping metadata generation as no language was provided")

    if args.upload:
        _upload_metadata_to_hf(
            repo_id=args.repo_id,
            token=str(token),
            hf_dir=hf_dir,
        )


if __name__ == "__main__":
    metadata_updater()
