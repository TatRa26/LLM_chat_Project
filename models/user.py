from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database.chat_db import Base

class User(Base):
    """Модель для таблицы users"""

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    messages = relationship("ChatHistory", back_populates="user")
