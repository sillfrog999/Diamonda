from dataclasses import dataclass

@dataclass(frozen=True)
class AdapterInfo:
    app_id: str
    display_name: str
    status: str
    note: str

class AdapterRegistry:
    """Registry for app integrations. No adapter is enabled until implemented and tested."""
    def __init__(self):
        self._items = {
            "youtube": AdapterInfo("youtube", "YouTube", "cdp-web", "Hỗ trợ mod website qua CDP; desktop native chưa hỗ trợ."),
            "facebook": AdapterInfo("facebook", "Facebook", "cdp-web", "Hỗ trợ mod website qua CDP; desktop native chưa hỗ trợ."),
            "discord": AdapterInfo("discord", "Discord", "cdp-web", "Hỗ trợ mod website qua CDP; desktop native chưa hỗ trợ."),
            "spotify": AdapterInfo("spotify", "Spotify", "cdp-web", "Hỗ trợ mod website qua CDP; desktop native chưa hỗ trợ."),
        }

    def get(self, app_id: str):
        return self._items.get(app_id)

    def all(self):
        return list(self._items.values())
