from abc import ABC, abstractmethod


class IntegrationAuthError(Exception):
    """Raised when credentials are invalid or access is denied."""
    pass


class IntegrationAdapter(ABC):

    @abstractmethod
    async def connect(self, credentials: dict) -> bool:
        """
        Validate credentials against the external API.
        Returns True on success.
        Raises IntegrationAuthError if credentials are invalid.
        """
        pass

    @abstractmethod
    async def collect_evidence(self) -> list[dict]:
        """
        Fetch raw data from the external system.
        Must handle pagination and rate limiting internally.
        Returns list of raw dicts tagged with a '_type' key.
        """
        pass

    @abstractmethod
    def normalize(self, raw_data: list[dict]) -> list[dict]:
        """
        Convert raw API data into normalized evidence records.
        Each record must contain: integration, control, evidence_type,
        source_id, timestamp, data.
        """
        pass
