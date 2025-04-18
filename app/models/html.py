from sqlalchemy import Column, Integer, Text, String, DateTime

from app.database import Base


class HTMLFile(Base):
    __tablename__ = "html_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)  # Храним HTML как текст
    source_pdf_id = Column(Integer, nullable=True)  # Связь с исходным PDF
    upload_date = Column(DateTime)
    file_size = Column(Integer)