from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database.chat_db import Base


class ChatHistory(Base):
    """Модель для таблицы chat_history"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    user = relationship("User", back_populates="messages")
