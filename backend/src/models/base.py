"""
Shared SQLAlchemy base for all models.
"""

from sqlalchemy.ext.declarative import declarative_base

# Shared base class for all SQLAlchemy models
Base = declarative_base()
