from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ✅ Register ALL models automatically
from app.models import *