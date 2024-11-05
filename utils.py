import os

from dotenv import load_dotenv


def _get_huggingface_token(provided_token: str | None = None) -> str:
    """
    Retrieves the HuggingFace token either from the provided argument or environment variables

    Args:
        provided_token (str | None): The token passed as an argument

    Returns:
        str: The HuggingFace token
    """

    if provided_token:
        return provided_token

    load_dotenv()
    token = os.getenv("HF_TOKEN")

    if token:
        print("Using token from environment variables")
        return token

    raise ValueError(
        "HuggingFace token is required either as an argument --token or an environment variable HF_TOKEN"
    )
