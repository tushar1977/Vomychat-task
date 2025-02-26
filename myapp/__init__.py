from flask import Flask, current_app
from flask_bcrypt import Bcrypt
from flask_jwt_extended.jwt_manager import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

from .config import Config as conf

load_dotenv()

db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)


def create_app(app_config=None):
    app = Flask(__name__)

    if app_config:
        app.config.update(app_config)
    app.config.from_object(conf)

    db.init_app(app)
    Migrate(app, db)

    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    from .routes import backend

    app.register_blueprint(backend, url_prefix="/api")

    return app
