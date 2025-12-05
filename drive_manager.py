import io
import re
from typing import Tuple

from googleapiclient.http import MediaIoBaseDownload


class DriveManager:
    """Handles downloading files from Google Drive."""

    def __init__(self, service):
        self.service = service

    def _extract_id(self, url: str) -> str:
        """Extracts file ID from various Google Drive URL formats."""
        patterns = [
            r'/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"Could not parse Drive ID from URL: {url}")

    def download_file(self, file_url: str) -> Tuple[bytes, str]:
        """Downloads a file into memory and returns (bytes, filename)."""
        file_id = self._extract_id(file_url)

        # Get Metadata (Name)
        meta = self.service.files().get(fileId=file_id, fields='name').execute()
        filename = meta.get('name', 'attachment.pdf')

        # Download Content
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        return fh.read(), filename