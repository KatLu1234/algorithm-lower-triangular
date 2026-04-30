from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import crud, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve items.
    """
    items = crud.item.get_multi(skip=skip, limit=limit)
    return items

@router.post("/", response_model=schemas.Item)
def create_item(*, item_in: schemas.ItemCreate) -> Any:
    """
    Create new item.
    """
    item = crud.item.create(obj_in=item_in)
    return item

@router.get("/{id}", response_model=schemas.Item)
def read_item(*, id: int) -> Any:
    """
    Get item by ID.
    """
    item = crud.item.get(id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{id}", response_model=schemas.Item)
def update_item(*, id: int, item_in: schemas.ItemUpdate) -> Any:
    """
    Update an item.
    """
    item = crud.item.get(id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = crud.item.update(db_obj=item, obj_in=item_in)
    return item

@router.delete("/{id}", response_model=schemas.Item)
def delete_item(*, id: int) -> Any:
    """
    Delete an item.
    """
    item = crud.item.get(id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = crud.item.remove(id=id)
    return item
