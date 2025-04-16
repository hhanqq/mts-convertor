from sqlalchemy import Boolean, Column, String, Integer
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    surname = Column(String)
    hashed_password = Column(String)
    email = Column(String, nullable=False, index=True, unique=True)
    tg_id = Column(String, unique=True)
    disabled = Column(Boolean, default=False)
