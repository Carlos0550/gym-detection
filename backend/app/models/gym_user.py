"""Modelo GymUser: tabla intermedia N:M entre User y Gym con un rol por gym."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import GymUserRole
from app.models.gym import Gym
from app.models.user import User


class GymUser(Base):
    __tablename__ = "gym_users"
    __table_args__ = (UniqueConstraint("gym_id", "user_id", name="uq_gym_user"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    gym_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gyms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[GymUserRole] = mapped_column(
        SAEnum(GymUserRole, name="gym_user_role", native_enum=True),
        nullable=False,
        default=GymUserRole.OPERATOR,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="gym_memberships")
    gym: Mapped[Gym] = relationship(back_populates="user_links")

    def __repr__(self) -> str:
        return f"<GymUser gym={self.gym_id} user={self.user_id} role={self.role}>"
