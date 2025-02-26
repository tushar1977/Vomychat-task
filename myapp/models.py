from . import db
import re
import uuid
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Mapped


@dataclass
class User(db.Model):
    id: Mapped[str] = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = db.Column(db.String(80), unique=True, nullable=False)
    email: Mapped[str] = db.Column(db.String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = db.Column(db.String(128), nullable=False)
    referral_code: Mapped[str] = db.Column(
        db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    referred_by: Mapped[str] = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=True
    )
    created_at: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now)

    referrals = db.relationship(
        "User", backref=db.backref("referrer", remote_side=[id])
    )
    reset_token: Mapped[str] = db.Column(db.String(36), unique=True, nullable=True)
    reset_token_expires: Mapped[datetime] = db.Column(db.DateTime, nullable=True)


@dataclass
class Referral(db.Model):
    id: Mapped[str] = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    referrer_id: Mapped[str] = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False
    )
    referred_user_id: Mapped[str] = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False
    )
    date_referred: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now)
    status: Mapped[str] = db.Column(db.String(20), default="successful")

    referrer = db.relationship("User", foreign_keys=[referrer_id])
    referred_user = db.relationship("User", foreign_keys=[referred_user_id])


@dataclass
class Reward(db.Model):
    id: Mapped[str] = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False
    )
    referral_id: Mapped[str] = db.Column(
        db.String(36), db.ForeignKey("referral.id"), nullable=False
    )
    reward_type: Mapped[str] = db.Column(db.String(50), nullable=False)
    amount: Mapped[float] = db.Column(db.Float, nullable=True)
    description: Mapped[str] = db.Column(db.String(255), nullable=True)
    awarded_at: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User")
    referral = db.relationship("Referral")


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


def get_user_by_referral_code(referral_code):
    return User.query.filter_by(referral_code=referral_code).first()


def generate_reset_token():
    return str(uuid.uuid4())
