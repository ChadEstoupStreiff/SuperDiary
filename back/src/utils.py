import mimetypes


def guess_mime(file_name: str) -> str:
    """
    Guess the MIME type of a file based on its name, with custom overrides.
    """
    ext = file_name.lower().split(".")[-1]

    custom_mime = {
        "md": "text/markdown",
        "markdown": "text/markdown",
        "env": "text/env",
        "yaml": "text/x-yaml",
        "yml": "text/x-yaml",
        "toml": "text/toml",
        "ipynb": "application/x-ipynb+json",
        "jsonl": "application/x-ndjson",
        "log": "text/log",
        "logs": "text/log",
    }

    if ext in custom_mime:
        return custom_mime[ext]

    mime, _ = mimetypes.guess_type(file_name)
    return mime or "application/octet-stream"
