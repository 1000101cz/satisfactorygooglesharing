import re
import requests
from typing import Tuple, Optional
from loguru import logger
from .settings import app_settings


SATISFACTORY_APP_ID = 526870


def get_steam_id_from_url(profile_url: str) -> Optional[str]:
        """
        :param profile_url:     can be Steam ID | https://steamcommunity.com/profiles/76561198000000000 | https://steamcommunity.com/id/username
        """
        value = profile_url.strip().rstrip("/")

        # User entered Steam ID directly
        if value.isdigit() and len(value) == 17:
            return value

        # Case /profiles/7656119...
        direct_match = re.search(r"/profiles/(\d{17})", value)
        if direct_match:
            return direct_match.group(1)

        # Case /id/custom_name or just custom_name
        custom_match = re.search(r"/id/([^/]+)", value)
        custom_name = custom_match.group(1) if custom_match else value.split("/")[-1]

        # Get Steam ID
        url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={app_settings.steam_api_key}&vanityurl={custom_name}"
        try:
            res = requests.get(url, timeout=5).json()
            if res.get("response", {}).get("success") == 1:
                return res["response"]["steamid"]
        except Exception:
            pass

        return None


def is_friend_playing_satisfactory(steam_id: str) -> Tuple[bool, str, Optional[str]]:
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={app_settings.steam_api_key}&steamids={steam_id}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        players = data.get("response", {}).get("players", [])

        if not players:
            return False

        player = players[0]
        persona_name = player.get("personaname", "Friend")
        
        current_game_id = player.get("gameid")
        current_game_name = player.get("gameextrainfo")

        # Compare with Satisfactory AppID (526870)
        if str(current_game_id) == str(SATISFACTORY_APP_ID):
            return True

        return False

    except Exception as e:
        logger.error(f"Friend activity detection error:")
        logger.exception(e)
        return False