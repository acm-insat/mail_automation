import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Central configuration loading from .env"""
    # We use os.getenv() to read the .env file.
    # The second argument is a fallback default if the .env var is missing.
    SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID")
    TAB_NAME: str = os.getenv("SHEET_TAB_NAME", "Sheet1")

    # Convert strings to Path objects for better file handling
    SIGNATURE_IMAGE_PATH: Path = Path(os.getenv("SIGNATURE_IMAGE_FILE", "signature.png"))
    CREDENTIALS_FILE: Path = Path(os.getenv("CREDENTIALS_FILE", "credentials.json"))
    TOKEN_FILE: Path = Path(os.getenv("TOKEN_FILE", "token.json"))
    TEMPLATE_FILE: Path = Path(os.getenv("TEMPLATE_FILE", "email_template.html"))

    FORM_LINK: str = os.getenv("FORM_LINK", "#")

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    @classmethod
    def validate(cls):
        """Checks if critical config is missing."""
        if not cls.SPREADSHEET_ID:
            raise ValueError("Missing SPREADSHEET_ID in .env file")
        if not cls.TEMPLATE_FILE.exists():
            raise FileNotFoundError(f"Template file not found: {cls.TEMPLATE_FILE}")