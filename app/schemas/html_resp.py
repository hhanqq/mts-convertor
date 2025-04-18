from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HTMLFileResponse(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    file_size: int
    source_pdf_id: Optional[int] = None

    class Config:
        orm_mode = True


class HTMLFileCreate(BaseModel):
    filename: str
    content: str
    source_pdf_id: Optional[int] = None