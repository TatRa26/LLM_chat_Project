import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from configs import config

logger = logging.getLogger(__name__)

# Подключение к базе данных через SQLAlchemy
engine = create_engine(config.postgres_url, echo=False)
session_local = sessionmaker(bind=engine, autocommit=False)
Base = declarative_base()


def get_db():
    session = session_local()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.exception(f'Error in getting session: {e}')
    finally:
        session.close()
