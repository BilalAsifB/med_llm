import random
import string

import tiktoken

from crawl4ai import (
    BrowserConfig,
    JsonCssExtractionStrategy
)


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Recursively merge two dictionaries with list handling."""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key] = result[key] + value
            else:
                result[key] = value
        else:
            result[key] = value

    return result


def generate_random_hex(length: int) -> str:
    """Generate a random hex string of specified length.

    Args:
        length: The desired length of the hex string.

    Returns:
        str: Random hex string of the specified length.
    """

    hex_chars = string.hexdigits.lower()
    return "".join(random.choice(hex_chars) for _ in range(length))


def clip_tokens(text: str, max_tokens: int, model_id: str) -> str:
    """Clip the text to a maximum number of tokens using the tiktoken tokenizer.

    Args:
        text: The input text to clip.
        max_tokens: Maximum number of tokens to keep (default: 8192).
        model_id: The model name to determine encoding (default: "gpt-4").

    Returns:
        str: The clipped text that fits within the token limit.
    """

    try:
        encoding = tiktoken.encoding_for_model(model_id)
    except KeyError:
        # Fallback to cl100k_base encoding (used by gpt-4, gpt-3.5-turbo, text-embedding-ada-002)
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text

    return encoding.decode(tokens[:max_tokens])


def get_browser_config() -> dict:
    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True,
    )


def get_json_extraction_strategy() -> JsonCssExtractionStrategy:
    schema = {
        "name": "Medicines",
        "baseSelector": ".page-banner_productContainer__vluxa",
        "fields": [
            {
                "name": "name",
                "selector": "h1.MuiTypography-root",
                "type": "text"
            },
            {
                "name": "price",
                "selector": "h2.productDetail_price__SAL9I",
                "type": "text"
            },
            {
                "name": "specification",
                "selector": "#SPECIFICATION",
                "type": "text"
            },
            {
                "name": "uasge_and_safety",
                "selector": "#USAGE\ AND\ SAFETY",
                "type": "text"
            },
            {
                "name": "precautions",
                "selector": "#PRECAUTIONS",
                "type": "text"
            },
            {
                "name": "warnings",
                "selector": "#WARNINGS",
                "type": "text"
            },
            {
                "name": "additional_information",
                "selector": "#ADDITIONAL\ INFORMATION",
                "type": "text"
            },
        ]
    }

    return JsonCssExtractionStrategy(
        schema=schema,
        verbose=True,
    )