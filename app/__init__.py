from flask import Flask

from app.config import Config, INSTANCE_DIR, UPLOADS_DIR
from app.extensions import db, login_manager
from app.routes import main_bp


def create_app(config_class=Config):
    app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
    app.config.from_object(config_class)

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app import models, service_models  # noqa: F401

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Базы данных и таблицы созданы.")

    app.register_blueprint(main_bp)

    return app
