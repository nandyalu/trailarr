"""
Plex media extras module.

Handles checking for media extras (trailers, behind-the-scenes, etc.) in Plex libraries.
"""

import aiohttp
from typing import Dict, Any, List
import json

import logging

logging = logging.getLogger("PlexExtras")


async def check_for_extras(
    token: str, 
    server_address: str, 
    media_type: str, 
    tmdb_id: str = None, 
    tvdb_id: str = None
) -> Dict[str, Any]:
    """
    Check if a media item has associated extras in Plex.
    
    Args:
        token: Authenticated Plex token
        server_address: Plex server address (e.g., "http://localhost:32400")
        media_type: Type of media ("movie" or "show")
        tmdb_id: TMDB ID of the media item
        tvdb_id: TVDB ID of the media item (for TV shows)
        
    Returns:
        Dict containing:
        - has_extras: Boolean indicating if extras were found
        - extras: List of extra details if they exist
        - message: Status message
        
    Raises:
        Exception: If the request fails
    """
    if not tmdb_id and not tvdb_id:
        raise Exception("Either tmdb_id or tvdb_id must be provided")
    
    logging.info(f"Checking for extras for {media_type} with TMDB ID: {tmdb_id}, TVDB ID: {tvdb_id}")
    
    # Clean up server address
    if not server_address.startswith(("http://", "https://")):
        server_address = f"http://{server_address}"
    
    if server_address.endswith("/"):
        server_address = server_address[:-1]
    
    headers = {
        "Accept": "application/json",
        "X-Plex-Token": token
    }
    
    try:
        # First, get all library sections
        sections_url = f"{server_address}/library/sections"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(sections_url, headers=headers) as response:
                if response.status == 401:
                    logging.error("Plex authentication failed - invalid token")
                    raise Exception("Plex authentication failed - invalid token")
                elif response.status != 200:
                    error_text = await response.text()
                    logging.error(f"Failed to get Plex library sections: {response.status} - {error_text}")
                    raise Exception(f"Failed to get Plex library sections: {response.status}")
                
                sections_data = await response.json()
                
                # Find relevant sections based on media type
                relevant_sections = []
                for section in sections_data.get("MediaContainer", {}).get("Directory", []):
                    section_type = section.get("type")
                    if (media_type == "movie" and section_type == "movie") or \
                       (media_type == "show" and section_type == "show"):
                        relevant_sections.append(section.get("key"))
                
                if not relevant_sections:
                    logging.info(f"No {media_type} sections found in Plex library")
                    return {
                        "has_extras": False,
                        "extras": [],
                        "message": f"No {media_type} sections found in Plex library"
                    }
                
                # Search for the media item in relevant sections
                for section_key in relevant_sections:
                    # Search by title/ID - this is a simplified approach
                    # In production, you might want to use Plex's search API or match by GUID
                    search_url = f"{server_address}/library/sections/{section_key}/all"
                    
                    async with session.get(search_url, headers=headers) as search_response:
                        if search_response.status != 200:
                            continue
                        
                        search_data = await search_response.json()
                        media_items = search_data.get("MediaContainer", {}).get("Metadata", [])
                        
                        # Look for matching media item
                        for item in media_items:
                            # Check if this item matches our TMDB/TVDB ID
                            # This is simplified - in production you'd check GUIDs more thoroughly
                            guids = item.get("Guid", [])
                            item_tmdb_id = None
                            item_tvdb_id = None
                            
                            for guid in guids:
                                guid_id = guid.get("id", "")
                                if "themoviedb" in guid_id:
                                    item_tmdb_id = guid_id.split("://")[-1].split("?")[0]
                                elif "thetvdb" in guid_id:
                                    item_tvdb_id = guid_id.split("://")[-1].split("?")[0]
                            
                            # Check if this is our target item
                            if (tmdb_id and item_tmdb_id == tmdb_id) or \
                               (tvdb_id and item_tvdb_id == tvdb_id):
                                
                                # Get detailed item info including extras
                                item_key = item.get("key")
                                if item_key:
                                    item_url = f"{server_address}{item_key}"
                                    
                                    async with session.get(item_url, headers=headers) as item_response:
                                        if item_response.status != 200:
                                            continue
                                        
                                        item_data = await item_response.json()
                                        item_details = item_data.get("MediaContainer", {}).get("Metadata", [])
                                        
                                        if item_details:
                                            # Check for extras
                                            extras = []
                                            for detail in item_details:
                                                # Look for extras in the item
                                                if "Extras" in detail:
                                                    for extra in detail["Extras"]:
                                                        extras.append({
                                                            "title": extra.get("title", ""),
                                                            "type": extra.get("subtype", ""),
                                                            "duration": extra.get("duration", 0)
                                                        })
                                            
                                            has_extras = len(extras) > 0
                                            logging.info(f"Found {len(extras)} extras for media item")
                                            
                                            return {
                                                "has_extras": has_extras,
                                                "extras": extras,
                                                "message": f"Found {len(extras)} extras" if has_extras else "No extras found"
                                            }
                
                # If we get here, the media item wasn't found
                logging.info(f"Media item not found in Plex library")
                return {
                    "has_extras": False,
                    "extras": [],
                    "message": "Media item not found in Plex library"
                }
                
    except aiohttp.ClientError as e:
        logging.error(f"Network error during extras check: {e}")
        raise Exception(f"Network error during extras check: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during extras check: {e}")
        raise