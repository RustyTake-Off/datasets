import argparse

from src.data_uploader import data_uploader
from src.gnu_docs.gnu_docs import main as gnu_docs_main
from src.metadata_updater import metadata_updater
from src.python_docs.python_docs import main as python_docs_main

# Language names
LANGUAGE_HANDLERS = {
    "python": python_docs_main,
    "gnu": gnu_docs_main,
}


def main():
    parser = argparse.ArgumentParser(description="Lang-Docs CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for uploading data
    upload_parser = subparsers.add_parser(
        "data",
        help="Upload data to HuggingFace",
    )
    upload_parser.add_argument(
        "lang",
        type=str,
        help="Docs lang directory containing dataset files (e.g. 'python', 'javascript')",
    )
    upload_parser.add_argument(
        "repo_id",
        type=str,
        help="HuggingFace repository id (e.g. 'example-org/example-repo')",
    )
    upload_parser.add_argument(
        "--token",
        type=str,
        help="HuggingFace token with user write access to repositories and PRs",
    )

    # Subparser for updating metadata
    metadata_parser = subparsers.add_parser(
        "metadata",
        help="Update metadata for repository",
    )
    metadata_parser.add_argument(
        "repo_id",
        type=str,
        help="HuggingFace repository id (e.g. 'example-org/example-repo')",
    )
    metadata_parser.add_argument(
        "--token",
        type=str,
        help="HuggingFace token with user write access to repositories and PRs",
    )

    # Subparser for language-specific processing
    lang_parser = subparsers.add_parser(
        "lang",
        help="Process language-specific docs",
    )
    lang_parser.add_argument(
        "lang",
        type=str,
        help="Specify docs lang for precessing (e.g. 'python', 'javascript') ",
    )
    args = parser.parse_args()

    # Process commands
    if args.command == "data":
        data_uploader(lang=args.lang, repo_id=args.repo_id, token=args.token)
    elif args.command == "metadata":
        metadata_updater(repo_id=args.repo_id, token=args.token)
    elif args.command == "lang":
        if args.lang in LANGUAGE_HANDLERS.keys():
            LANGUAGE_HANDLERS[args.lang]()
        else:
            raise ValueError(
                f"Specified docs lang is not supported. Available values: {', '.join([docs_lang for docs_lang in LANGUAGE_HANDLERS.keys()])}"
            )


if __name__ == "__main__":
    main()
