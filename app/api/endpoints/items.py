from typing import Any, List
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from app import crud, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.Item])
def read_items(
    db: Client = Depends(deps.get_supabase),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve items.
    """
    items = crud.item.get_multi(db, skip=skip, limit=limit)
    return items

@router.post("/", response_model=schemas.Item)
def create_item(
    *,
    db: Client = Depends(deps.get_supabase),
    item_in: schemas.ItemCreate
) -> Any:
    """
    Create new item.
    """
    item = crud.item.create(db, obj_in=item_in)
    return item

@router.get("/{id}", response_model=schemas.Item)
def read_item(
    *,
    db: Client = Depends(deps.get_supabase),
    id: int
) -> Any:
    """
    Get item by ID.
    """
    item = crud.item.get(db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{id}", response_model=schemas.Item)
def update_item(
    *,
    db: Client = Depends(deps.get_supabase),
    id: int,
    item_in: schemas.ItemUpdate
) -> Any:
    """
    Update an item.
    """
    item = crud.item.get(db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = crud.item.update(db, id=id, obj_in=item_in)
    return item

@router.delete("/{id}", response_model=schemas.Item)
def delete_item(
    *,
    db: Client = Depends(deps.get_supabase),
    id: int
) -> Any:
    """
    Delete an item.
    """
    item = crud.item.get(db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = crud.item.remove(db, id=id)
    return item
