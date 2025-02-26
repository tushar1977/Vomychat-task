from datetime import datetime, timedelta
from flask import request, jsonify, Blueprint
from flask_login.login_manager import current_app
from .models import (
    is_valid_email,
    User,
    Reward,
    Referral,
    is_strong_password,
    get_user_by_referral_code,
    generate_reset_token,
)
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from . import db, limiter, bcrypt, mail
from flask_mail import Message
import os

backend = Blueprint("backend", __name__)


def send_mail(subject, body, recipients):
    mail_msg = Message(
        subject, sender=os.environ.get("MAIL_SENDER_EMAIL"), recipients=recipients
    )
    mail_msg.body = body
    mail.send(mail_msg)


@backend.route("/", methods=["GET"])
@limiter.limit("10 per hour")
def ping():
    return jsonify({"message": "status OK server running"}, 200)


@backend.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data = request.get_json()

    if (
        not data
        or not data.get("email")
        or not data.get("username")
        or not data.get("password")
    ):
        return jsonify({"message": "Missing required fields"}), 400

    if not is_valid_email(data["email"]):
        return jsonify({"message": "Invalid email format"}), 400

    if not is_strong_password(data["password"]):
        return jsonify(
            {
                "message": "Password must be at least 8 characters and contain uppercase, lowercase, number, and special character"
            }
        ), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already in use"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"message": "Username already in use"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user = User(
        username=data["username"], email=data["email"], password_hash=hashed_password
    )

    referrer = None
    if "referral_code" in data and data["referral_code"]:
        referrer = get_user_by_referral_code(data["referral_code"])
        if referrer:
            new_user.referred_by = referrer.id
        else:
            return jsonify({"message": "Invalid referral code"}), 400

    try:
        db.session.add(new_user)
        db.session.commit()

        if referrer:
            referral = Referral(referrer_id=referrer.id, referred_user_id=new_user.id)
            db.session.add(referral)
            db.session.commit()

            reward = Reward(
                user_id=referrer.id,
                referral_id=referral.id,
                reward_type="credit",
                amount=10.0,
                description="Referral bonus",
            )
            db.session.add(reward)
            db.session.commit()

    except Exception as _:
        db.session.rollback()
        return jsonify({"error": "An error occurred while processing referral"}), 500
    return jsonify(
        {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "referral_code": new_user.referral_code,
        }
    ), 201


@backend.route("/login", methods=["POST"])
@limiter.limit("20 per hour")
def login():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Missing request data"}), 400

    identifier = data.get("identifier")
    password = data.get("password")

    if not identifier or not password:
        return jsonify({"message": "Missing identifier or password"}), 400

    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)

    resp = jsonify({"message": "Login successful", "user_id": user.id})
    resp.set_cookie(
        "access_token_cookie",
        access_token,
        httponly=True,
        secure=current_app.config["JWT_COOKIE_SECURE"],
        samesite=current_app.config["JWT_COOKIE_SAMESITE"],
    )

    return resp, 200


@backend.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    data = request.get_json()

    if not data or not data.get("email"):
        return jsonify({"message": "Email is required"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify(
            {
                "message": "If this email is registered, a password reset link will be sent"
            }
        ), 200

    reset_token = generate_reset_token()
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now() + timedelta(hours=1)
    db.session.commit()

    reset_url = f"/reset-password?token={reset_token}"

    # To be used in production
    # try:

    # send_reset_email(user.email, reset_url)
    # except Exception as e:
    #    db.session.rollback()
    #    return jsonify({"message": "Failed to send reset email"}), 500

    return jsonify(
        {
            "message": "Password reset link sent",
            "reset_url": reset_url,
        }
    ), 200


@backend.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    token = request.args.get("token")
    if not data or not token or not data.get("new_password"):
        return jsonify({"message": "Token and new password are required"}), 400

    user = User.query.filter_by(reset_token=token).first()

    if not user:
        return jsonify({"message": "Invalid or expired token"}), 400

    if user.reset_token_expires < datetime.now():
        return jsonify({"message": "Token has expired"}), 400

    user.password_hash = bcrypt.generate_password_hash(data["new_password"]).decode(
        "utf-8"
    )
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()

    return jsonify({"message": "Password reset successfully"}), 200


@backend.route("/referrals", methods=["GET"])
@jwt_required()
def get_referrals():
    current_user_id = get_jwt_identity()

    referrals = Referral.query.filter_by(referrer_id=current_user_id).all()

    result = []
    for referral in referrals:
        referred_user = User.query.get(referral.referred_user_id)
        result.append(
            {
                "id": referral.id,
                "username": referred_user.username,
                "date_referred": referral.date_referred.isoformat(),
                "status": referral.status,
            }
        )

    return jsonify({"referrals": result}), 200


@backend.route("/referral-stats", methods=["GET"])
@jwt_required()
def get_referral_stats():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    referral_count = Referral.query.filter_by(
        referrer_id=current_user_id, status="successful"
    ).count()

    rewards = Reward.query.filter_by(user_id=current_user_id).all()
    total_credits = sum(
        reward.amount for reward in rewards if reward.reward_type == "credit"
    )

    return (
        jsonify(
            {
                "total_referrals": referral_count,
                "total_credits": total_credits,
                "referral_code": user.referral_code,
                "referral_link": f"{request.host_url}register?referral={user.referral_code}",
            }
        ),
        200,
    )


@backend.route("/logout", methods=["POST"])
def logout():
    resp = jsonify({"message": "Logout successful"})
    resp.set_cookie("access_token_cookie", "", expires=0)
    return resp, 200
