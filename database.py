import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# например: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:zxc011@localhost:5432/mydatabase")

# connect_args не нужен для PostgreSQL
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()