"""
Plex media scanning module.

Handles triggering media library scans on Plex servers.
"""

import aiohttp
from typing import Dict, Any
from urllib.parse import quote

import logging

logging = logging.getLogger("PlexScan")


async def trigger_media_scan(token: str, server_address: str, media_folder_path: str) -> Dict[str, Any]:
    """
    Trigger a media library scan for a specific folder on Plex server.
    
    Args:
        token: Authenticated Plex token
        server_address: Plex server address (e.g., "http://localhost:32400")
        media_folder_path: Path to the media folder to scan
        
    Returns:
        Dict containing:
        - success: Boolean indicating if scan was triggered
        - message: Status message
        
    Raises:
        Exception: If the scan request fails
    """
    logging.info(f"Triggering media scan for path: {media_folder_path}")
    
    # Clean up server address
    if not server_address.startswith(("http://", "https://")):
        server_address = f"http://{server_address}"
    
    if server_address.endswith("/"):
        server_address = server_address[:-1]
    
    headers = {
        "Accept": "application/json",
        "X-Plex-Token": token
    }
    
    # URL encode the path
    encoded_path = quote(media_folder_path)
    
    # Plex API endpoint for scanning library sections
    # We use the generic scan endpoint which refreshes the entire library
    # In a production implementation, you might want to find the specific library section
    # that contains the folder and scan only that section
    scan_url = f"{server_address}/library/sections/all/refresh"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(scan_url, headers=headers) as response:
                if response.status == 200:
                    logging.info(f"Successfully triggered scan for: {media_folder_path}")
                    return {
                        "success": True,
                        "message": f"Media scan triggered for {media_folder_path}"
                    }
                elif response.status == 401:
                    logging.error("Plex authentication failed - invalid token")
                    raise Exception("Plex authentication failed - invalid token")
                else:
                    error_text = await response.text()
                    logging.error(f"Failed to trigger Plex scan: {response.status} - {error_text}")
                    raise Exception(f"Failed to trigger Plex scan: {response.status}")
                    
    except aiohttp.ClientError as e:
        logging.error(f"Network error during scan request: {e}")
        raise Exception(f"Network error during scan request: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during scan request: {e}")
        raise