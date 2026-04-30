from typing import List, Optional
from app.schemas.item import ItemCreate, ItemUpdate

# Dummy database
db = []

class CRUDItem:
    def get(self, id: int) -> Optional[dict]:
        for item in db:
            if item["id"] == id:
                return item
        return None

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[dict]:
        return db[skip : skip + limit]

    def create(self, obj_in: ItemCreate) -> dict:
        item_id = len(db) + 1
        item = {
            "id": item_id,
            "title": obj_in.title,
            "description": obj_in.description,
        }
        db.append(item)
        return item

    def update(self, db_obj: dict, obj_in: ItemUpdate) -> dict:
        if obj_in.title:
            db_obj["title"] = obj_in.title
        if obj_in.description:
            db_obj["description"] = obj_in.description
        return db_obj

    def remove(self, id: int) -> Optional[dict]:
        for i, item in enumerate(db):
            if item["id"] == id:
                return db.pop(i)
        return None

item = CRUDItem()
