from sqlmodel import create_engine, SQLModel
from core.config import settings

engine = create_engine(settings.database_path, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
