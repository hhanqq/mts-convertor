from sqlalchemy import Column, String, Integer, LargeBinary

from app.database import Base


class PDFFile(Base):
    __tablename__ = "pdf_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(LargeBinary)
    upload_date = Column(String)
    file_size = Column(Integer)
