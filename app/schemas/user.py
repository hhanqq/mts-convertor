from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    first_name: str = Field(..., min_length=1, max_length=50, example="Sergey")
    last_name: str = Field(..., min_length=1, max_length=50, example="Dudnik")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="megaparol123")
    surname: Optional[str] = Field(None, max_length=50, example="Sergeevich")
    tg_id: str = Field(..., example="123456789")
    disabled: bool = Field(False)


class UserOut(UserBase):
    user_id: int = Field(..., example=1)
    first_name: str
    tg_id: str
    disabled: bool


