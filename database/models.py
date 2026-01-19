"""Модели данных для базы данных."""
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class User(Base):
    """Модель пользователя бота."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(nullable=True)
    cycle_length: Mapped[int] = mapped_column(default=28)  # Длина цикла в днях (по умолчанию 28)
    last_period_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)  # Дата последних месячных
    notification_enabled: Mapped[bool] = mapped_column(default=True)  # Включены ли уведомления
    notification_time: Mapped[Optional[str]] = mapped_column(nullable=True, default="09:00")  # Время уведомлений (формат HH:MM)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    partners: Mapped[list["Partner"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    cycle_entries: Mapped[list["CycleEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Partner(Base):
    """Модель партнера пользователя для получения уведомлений."""
    
    __tablename__ = "partners"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="partners")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="partner", cascade="all, delete-orphan")


class CycleEntry(Base):
    """Модель записи о дне цикла пользователя."""
    
    __tablename__ = "cycle_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day_number: Mapped[int] = mapped_column()  # Номер дня цикла (1-28/30)
    entry_date: Mapped[datetime] = mapped_column(index=True)  # Дата записи
    phase: Mapped[str] = mapped_column()  # Фаза цикла (менструальная, фолликулярная, овуляторная, лютеиновая, пмс)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="cycle_entries")


class Notification(Base):
    """Модель уведомления пользователя или партнера."""
    
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    partner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("partners.id", ondelete="CASCADE"), nullable=True)
    notification_type: Mapped[str] = mapped_column()  # Тип уведомления (period_start, phase_change, etc.)
    sent_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")
    partner: Mapped[Optional["Partner"]] = relationship(back_populates="notifications")
