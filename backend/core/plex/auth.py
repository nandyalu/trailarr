"""
Plex authentication module.

Handles the Plex PIN-based OAuth authentication flow.
"""

import asyncio
import aiohttp
from typing import Dict, Any
from datetime import datetime, timedelta

import logging

logging = logging.getLogger("PlexAuth")

# Plex API endpoints
PLEX_PIN_URL = "https://plex.tv/api/v2/pins"
PLEX_TOKEN_URL = "https://plex.tv/api/v2/pins/{pin}"


async def start_auth_flow(client_identifier: str, product_name: str) -> Dict[str, Any]:
    """
    Start the Plex authentication flow by requesting a PIN.
    
    Args:
        client_identifier: Unique identifier for the client application
        product_name: Name of the product/application
        
    Returns:
        Dict containing:
        - pin: The PIN code for user authentication
        - auth_url: URL for user to visit for authentication
        - expires_in: Timestamp when the PIN expires
        
    Raises:
        Exception: If the PIN request fails
    """
    logging.info(f"Starting Plex auth flow for product: {product_name}")
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    data = {
        "X-Plex-Product": product_name,
        "X-Plex-Client-Identifier": client_identifier,
        "strong": "true"  # Use 4-digit PIN instead of 6-digit
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(PLEX_PIN_URL, headers=headers, data=data) as response:
                if response.status != 201:
                    error_text = await response.text()
                    logging.error(f"Failed to get PIN from Plex: {response.status} - {error_text}")
                    raise Exception(f"Failed to get PIN from Plex: {response.status}")
                
                result = await response.json()
                
                pin_data = {
                    "pin": result["code"],
                    "auth_url": f"https://app.plex.tv/auth#?clientID={client_identifier}&code={result['code']}&context%5Bdevice%5D%5Bproduct%5D={product_name}",
                    "expires_in": result["expiresAt"]
                }
                
                logging.info(f"Successfully generated PIN: {pin_data['pin']}")
                return pin_data
                
    except aiohttp.ClientError as e:
        logging.error(f"Network error during PIN request: {e}")
        raise Exception(f"Network error during PIN request: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during PIN request: {e}")
        raise


async def poll_for_token(pin: str) -> Dict[str, Any]:
    """
    Poll the Plex API to check if the user has authenticated with the PIN.
    
    Args:
        pin: The PIN code to check
        
    Returns:
        Dict containing:
        - status: "pending", "success", or "expired"
        - token: The authentication token (if successful)
        - plex_server_address: The Plex server address (if successful)
        
    Raises:
        Exception: If the polling request fails
    """
    logging.debug(f"Polling for token with PIN: {pin}")
    
    headers = {
        "Accept": "application/json",
    }
    
    url = PLEX_TOKEN_URL.format(pin=pin)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"Failed to poll token from Plex: {response.status} - {error_text}")
                    raise Exception(f"Failed to poll token from Plex: {response.status}")
                
                result = await response.json()
                
                # Check if PIN has expired
                expires_at = datetime.fromisoformat(result["expiresAt"].replace("Z", "+00:00"))
                if datetime.now().astimezone() > expires_at:
                    logging.info(f"PIN {pin} has expired")
                    return {"status": "expired"}
                
                # Check if token is available
                if result.get("authToken"):
                    logging.info(f"Successfully authenticated PIN: {pin}")
                    # In a real implementation, you would also get the server address
                    # For now, we'll use a placeholder
                    return {
                        "status": "success",
                        "token": result["authToken"],
                        "plex_server_address": "http://localhost:32400"  # This should be discovered
                    }
                else:
                    logging.debug(f"PIN {pin} still pending authentication")
                    return {"status": "pending"}
                    
    except aiohttp.ClientError as e:
        logging.error(f"Network error during token polling: {e}")
        raise Exception(f"Network error during token polling: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during token polling: {e}")
        raise