"""
User domain models: User, Role, Permission, UserRole, RolePermission, PasswordResetToken.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Boolean, String, Text, UniqueConstraint, ForeignKey, DateTime, Table, Column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from src.shared.base_model import AuditableBase, TenantMixin, GUID, SCHOOL_ID


# Association table for many-to-many: users <-> roles
user_roles = Table(
    "user_roles",
    AuditableBase.metadata,
    Column("user_id", PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for many-to-many: roles <-> permissions
role_permissions = Table(
    "role_permissions",
    AuditableBase.metadata,
    Column("role_id", PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", PG_UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(AuditableBase):
    """
    System-wide permission (not tenant-scoped).
    Examples: 'finance:view', 'students:edit', 'reports:generate'.
    """

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin",
    )


class Role(AuditableBase, TenantMixin):
    """
    Tenant-scoped role (school_id).
    Examples: 'Head Master', 'Finance Manager', 'Teacher', 'Parent'.
    """

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_roles_school_name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    permissions: Mapped[List[Permission]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )
    users: Mapped[List["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin",
    )


class User(AuditableBase, TenantMixin):
    """
    System user bound to a school (school_id).
    Supports multiple types: SUPERADMIN, ADMIN, STAFF, TEACHER, PARENT, STUDENT.
    """

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("school_id", "username", name="uq_users_school_username"),)

    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_login: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    roles: Mapped[List[Role]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    @property
    def scopes(self) -> List[str]:
        """Extract permission names from all assigned roles."""
        scopes = set()
        for role in self.roles:
            for permission in role.permissions:
                scopes.add(permission.name)
        return sorted(list(scopes))


class PasswordResetToken(AuditableBase):
    """
    One-time password reset token (not tenant-scoped).
    Expires after configured duration.
    """

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped[User] = relationship("User")
