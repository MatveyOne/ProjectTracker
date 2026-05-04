from datetime import UTC, datetime

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

from app.extensions import db, login_manager


def utc_now():
    # Возвращает текущее время в UTC для timestamp-полей.
    return datetime.now(UTC)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    projects = db.relationship("Project", back_populates="teacher", lazy=True)
    project_links = db.relationship("ProjectStudent", back_populates="student", lazy=True)
    progress_entries = db.relationship("Progress", back_populates="student", lazy=True)

    @property
    def full_name(self):
        # Старые записи без first/last не ломают отображение имени.
        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        if first and last:
            return f"{first} {last}"
        if first:
            return first
        if self.name:
            return self.name
        return self.email


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    teacher = db.relationship("User", back_populates="projects", lazy=True)
    stages = db.relationship(
        "Stage",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Stage.order_num",
        lazy=True,
    )
    student_links = db.relationship(
        "ProjectStudent",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy=True,
    )


class ProjectStudent(db.Model):
    __table_args__ = (
        UniqueConstraint("project_id", "student_id", name="uq_project_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    project = db.relationship("Project", back_populates="student_links", lazy=True)
    student = db.relationship("User", back_populates="project_links", lazy=True)


class Stage(db.Model):
    __table_args__ = (
        UniqueConstraint("project_id", "order_num", name="uq_project_stage_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    order_num = db.Column(db.Integer, nullable=False)

    project = db.relationship("Project", back_populates="stages", lazy=True)
    progress_entries = db.relationship(
        "Progress",
        back_populates="stage",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Progress(db.Model):
    __table_args__ = (
        UniqueConstraint("student_id", "stage_id", name="uq_student_stage_progress"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="not_started")
    github_url = db.Column(db.String(500))
    file_path = db.Column(db.String(500))
    comment = db.Column(db.Text)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    student = db.relationship("User", back_populates="progress_entries", lazy=True)
    stage = db.relationship("Stage", back_populates="progress_entries", lazy=True)


@login_manager.user_loader
def load_user(user_id):
    # Загружает пользователя по id из сессии Flask-Login.
    return db.session.get(User, int(user_id))
