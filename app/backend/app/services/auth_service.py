import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import hash_password, verify_password
from ..models.user import User
from ..repositories import user_repo

logger = logging.getLogger(__name__)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await user_repo.get_by_username(db, username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_admin_if_none(db: AsyncSession, username: str, password: str, email: str):
    """Create default admin user if no users exist in the database."""
    count = await user_repo.count(db)
    if count > 0:
        return
    logger.info(f"No users found. Creating default admin user: {username}")
    await user_repo.create(
        db,
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role="admin",
        is_active=True,
    )
