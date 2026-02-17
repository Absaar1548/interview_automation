from typing import Dict, Optional
from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str  # In a real app, this would be hashed!
    role: str = "candidate"

# Global in-memory storage
USERS: Dict[str, User] = {}

def create_user(username: str, password: str, role: str = "candidate") -> User:
    if username in USERS:
        raise ValueError("Username already exists")
    
    user = User(username=username, password=password, role=role)
    USERS[username] = user
    return user

def authenticate_user(username: str, password: str) -> Optional[User]:
    user = USERS.get(username)
    if user and user.password == password:
        return user
    return None

# Pre-seed with admin and candidate
create_user("admin", "admin", "hr")
create_user("candidate", "candidate", "candidate")
