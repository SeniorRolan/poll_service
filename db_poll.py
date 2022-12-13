from redis_om import (Field, HashModel, Migrator)
from typing import Optional
from pydantic import BaseModel


class Poll(HashModel):
    # Indexed for exact text matching
    name: str = Field(index=True, full_text_search=True, max_length=200)
    description: str = Field(index=True)
    # Indexed for numeric matching
    is_active: Optional[int] = 1
    is_deleted: Optional[int] = 0


class CreatePoll(BaseModel):
    name: str
    description: str


Migrator().run()


