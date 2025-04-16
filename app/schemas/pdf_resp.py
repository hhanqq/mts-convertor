from pydantic import BaseModel


class PDFResponse(BaseModel):
    id: int
    filename: str
    upload_date: str
    file_size: int
