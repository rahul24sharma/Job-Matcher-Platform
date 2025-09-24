# app/core/dependencies.py

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.session import get_db
from app.db.models import User
from app.core.security import decode_token, verify_password

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Optional OAuth2 scheme (doesn't require authentication)
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", 
    auto_error=False
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode the token
    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
        
        # Get email from token payload
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    Raises HTTPException if user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token is provided, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        if payload is None:
            return None
        
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        return user
        
    except (JWTError, AttributeError):
        return None

async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user if they are an admin.
    Raises HTTPException if user is not an admin.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> Optional[User]:
    """
    Authenticate a user by email and password.
    Returns User if authentication successful, None otherwise.
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

def get_user_by_email(
    db: Session,
    email: str
) -> Optional[User]:
    """
    Get a user by email address.
    Returns User if found, None otherwise.
    """
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(
    db: Session,
    user_id: int
) -> Optional[User]:
    """
    Get a user by ID.
    Returns User if found, None otherwise.
    """
    return db.query(User).filter(User.id == user_id).first()

def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_active: bool = True
) -> User:
    """
    Create a new user in the database.
    Returns the created User object.
    """
    from app.core.security import get_password_hash
    
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=is_active
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create empty profile for the user
    try:
        from app.db.models.profile import Profile
        profile = Profile(
            user_id=user.id,
            full_name=full_name
        )
        db.add(profile)
        db.commit()
    except Exception:
        # Profile creation is optional
        pass
    
    return user

def update_user_password(
    db: Session,
    user: User,
    new_password: str
) -> User:
    """
    Update a user's password.
    Returns the updated User object.
    """
    from app.core.security import get_password_hash
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    
    return user

def verify_user_password(
    user: User,
    password: str
) -> bool:
    """
    Verify a user's password.
    Returns True if password is correct, False otherwise.
    """
    return verify_password(password, user.hashed_password)

# Dependency aliases for backward compatibility
get_current_user_active = get_current_active_user
get_current_user_optional = get_optional_current_user