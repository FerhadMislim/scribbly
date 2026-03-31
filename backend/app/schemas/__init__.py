"""
Pydantic schemas for request/response validation.

Example schema:
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
```
"""
