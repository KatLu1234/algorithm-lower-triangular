from typing import Generator
from supabase import Client
from app.db.supabase import supabase

def get_supabase() -> Generator:
    try:
        yield supabase
    finally:
        pass
