from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.core import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    
    # Keycloak integration (Option 4: Federated Identity Pattern)
    keycloak_user_id = Column(String, unique=True, nullable=True, index=True)  # UUID from Keycloak
    last_synced_at = Column(DateTime, nullable=True)  # Last time user data was synced from Keycloak
    
    # Profile picture stored in MinIO
    profile_picture_url = Column(String, nullable=True)  # Object path/name in MinIO bucket
    
    # Relationship to the posts table
    posts = relationship("Post", back_populates="user")
    
    # Relationship to comments table
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    
    # Relationship to likes table
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', keycloak_user_id='{self.keycloak_user_id}')>"


