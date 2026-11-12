from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """Contract for future app-specific integrations.

    Adapters should use documented, user-controlled customization mechanisms.
    They must not bypass authentication, DRM, anti-cheat, or security controls.
    """

    app_id = "unknown"
    display_name = "Unknown application"

    @abstractmethod
    def detect(self) -> bool:
        """Return whether the supported app/client is present."""
        raise NotImplementedError

    @abstractmethod
    def validate_pack(self, manifest: dict) -> tuple[bool, str]:
        """Check whether a pack targets this adapter and is compatible."""
        raise NotImplementedError
