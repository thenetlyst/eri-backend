from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://exam_user:exam_password@localhost:5432/exam_platform"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("DB Connected:", result.scalar())
