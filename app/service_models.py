from datetime import datetime

from app.extensions import db


class Message(db.Model):
    __bind_key__ = "service"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    from_user_id = db.Column(db.Integer, nullable=False)
    to_user_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ActionLog(db.Model):
    __bind_key__ = "service"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer)
    action_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ApiLog(db.Model):
    __bind_key__ = "service"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
