from abc import ABC
from typing import Optional
from supabase import Client
from app.database.supabase_client import get_supabase_client


class BaseRepository(ABC):
    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()

    @property
    def client(self) -> Optional[Client]:
        return self._client
