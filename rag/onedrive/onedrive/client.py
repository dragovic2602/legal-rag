"""
Microsoft Graph API client for OneDrive access.
Uses MSAL for OAuth2 client credentials flow (app-only auth).
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional

import aiohttp
import msal
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".xlsx", ".xls", ".html", ".htm", ".md", ".txt", ".mp3",
}

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class OneDriveClient:
    """Microsoft Graph API client for OneDrive file operations."""

    def __init__(self):
        self.tenant_id = os.environ["AZURE_TENANT_ID"]
        self.client_id = os.environ["AZURE_CLIENT_ID"]
        self.client_secret = os.environ["AZURE_CLIENT_SECRET"]
        self.user_id = os.getenv("ONEDRIVE_USER_ID", "me")
        self.root_folder = os.getenv("ONEDRIVE_ROOT_FOLDER", "")
        self._token: Optional[str] = None
        self._msal_app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
        )

    async def authenticate(self) -> str:
        """Acquire an access token using client credentials flow."""
        result = self._msal_app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "unknown"))
            raise RuntimeError(f"MSAL token acquisition failed: {error}")
        self._token = result["access_token"]
        logger.info("Successfully authenticated with Microsoft Graph")
        return self._token

    async def _get_token(self) -> str:
        """Return cached token or acquire a new one."""
        if not self._token:
            await self.authenticate()
        return self._token

    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def _drive_root(self) -> str:
        """Build the base drive URL for the configured user."""
        if self.user_id == "me":
            return f"{GRAPH_BASE}/me/drive"
        return f"{GRAPH_BASE}/users/{self.user_id}/drive"

    async def get_delta(self, delta_link: Optional[str] = None) -> tuple[list[dict], str]:
        """
        Call the Graph delta API to get changed items since the last sync.

        Args:
            delta_link: Delta link from the previous sync; None for initial full scan.

        Returns:
            Tuple of (list of change items, new delta link string).
        """
        token = await self._get_token()
        headers = self._headers(token)

        if delta_link:
            url = delta_link
        else:
            root = self._drive_root()
            if self.root_folder:
                # Scope delta to a specific folder
                encoded = self.root_folder.strip("/").replace("/", "%2F")
                url = f"{root}/root:/{encoded}:/delta"
            else:
                url = f"{root}/root/delta"

        items: list[dict] = []
        new_delta_link: Optional[str] = None

        async with aiohttp.ClientSession() as session:
            while url:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        # Token expired — re-authenticate once
                        self._token = None
                        token = await self._get_token()
                        headers = self._headers(token)
                        async with session.get(url, headers=headers) as resp2:
                            data = await resp2.json()
                    else:
                        data = await resp.json()

                if "error" in data:
                    raise RuntimeError(f"Graph API error: {data['error']}")

                items.extend(data.get("value", []))

                if "@odata.nextLink" in data:
                    url = data["@odata.nextLink"]
                elif "@odata.deltaLink" in data:
                    new_delta_link = data["@odata.deltaLink"]
                    url = None
                else:
                    url = None

        return items, new_delta_link

    async def download_file(self, item_id: str, filename: str) -> str:
        """
        Download a file by its Graph item ID to a temporary directory.

        Args:
            item_id: Graph API item ID.
            filename: Original filename (used to preserve the extension).

        Returns:
            Absolute path to the downloaded temporary file.
        """
        token = await self._get_token()
        headers = self._headers(token)
        root = self._drive_root()
        url = f"{root}/items/{item_id}/content"

        suffix = Path(filename).suffix
        tmp_dir = tempfile.mkdtemp(prefix="onedrive_sync_")
        local_path = os.path.join(tmp_dir, filename)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, allow_redirects=True) as resp:
                if resp.status == 401:
                    self._token = None
                    token = await self._get_token()
                    headers = self._headers(token)
                    async with session.get(url, headers=headers, allow_redirects=True) as resp2:
                        content = await resp2.read()
                else:
                    content = await resp.read()

        with open(local_path, "wb") as f:
            f.write(content)

        logger.info(f"Downloaded {filename} ({len(content)} bytes) to {local_path}")
        return local_path

    def is_supported(self, filename: str) -> bool:
        """Return True if the file extension is supported for ingestion."""
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS
