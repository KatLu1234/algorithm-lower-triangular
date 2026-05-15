from typing import List, Optional, Any
from supabase import Client
from app.schemas.item import ItemCreate, ItemUpdate

class CRUDItem:
    def get(self, db: Client, id: int) -> Optional[dict]:
        response = db.table("items").select("*").eq("id", id).execute()
        return response.data[0] if response.data else None

    def get_multi(self, db: Client, skip: int = 0, limit: int = 100) -> List[dict]:
        response = db.table("items").select("*").range(skip, skip + limit - 1).execute()
        return response.data

    def create(self, db: Client, obj_in: ItemCreate) -> dict:
        data = obj_in.model_dump()
        response = db.table("items").insert(data).execute()
        return response.data[0]

    def update(self, db: Client, id: int, obj_in: ItemUpdate) -> dict:
        data = obj_in.model_dump(exclude_unset=True)
        response = db.table("items").update(data).eq("id", id).execute()
        return response.data[0]

    def remove(self, db: Client, id: int) -> Optional[dict]:
        response = db.table("items").delete().eq("id", id).execute()
        return response.data[0] if response.data else None

item = CRUDItem()
