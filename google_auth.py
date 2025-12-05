from typing import Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from config import Config


class GoogleAuth:
    """Handles Google OAuth2 authentication."""

    @staticmethod
    def get_services() -> Tuple[Resource, Resource, Resource]:
        creds = None
        if Config.TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(Config.TOKEN_FILE), Config.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Config.CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(f"Missing {Config.CREDENTIALS_FILE}")
                flow = InstalledAppFlow.from_client_secrets_file(str(Config.CREDENTIALS_FILE), Config.SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(Config.TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        return (
            build("gmail", "v1", credentials=creds),
            build("sheets", "v4", credentials=creds),
            build("drive", "v3", credentials=creds)
        )