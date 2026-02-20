from sqlmodel import create_engine, SQLModel
import os

DATABASE_URL = "sqlite:///storytrace.db"

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
