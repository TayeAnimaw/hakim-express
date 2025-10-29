#app/models/admin_role.py 
from sqlalchemy import (Column,BigInteger,String, TIMESTAMP,Text,ForeignKey
)
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime

class AdminRole(Base):
    __tablename__ = 'admin_roles'

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="admin_role", lazy="joined")
    permissions = relationship("AdminPermission", back_populates="admin", cascade="all, delete-orphan")
    activities = relationship("AdminActivity", back_populates="admin", cascade="all, delete-orphan")

class AdminPermission(Base):
    __tablename__ = 'admin_permissions'

    id = Column(BigInteger, primary_key=True, index=True)
    admin_id = Column(BigInteger, ForeignKey("admin_roles.id", ondelete="CASCADE"), nullable=False)
    permission = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    admin = relationship("AdminRole", back_populates="permissions")


class AdminActivity(Base):
    __tablename__ = 'admin_activities'

    id = Column(BigInteger, primary_key=True, index=True)
    admin_id = Column(BigInteger, ForeignKey("admin_roles.id", ondelete="CASCADE"), nullable=False)
    activity = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    admin = relationship("AdminRole", back_populates="activities")
