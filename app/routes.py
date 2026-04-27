from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import Progress, Project, Stage, User


main_bp = Blueprint("main", __name__)


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def get_teacher_project_or_404(project_id):
    project = db.session.get(Project, project_id)
    if project is None or project.teacher_id != current_user.id:
        abort(404)
    return project


def get_teacher_stage_or_404(stage_id):
    stage = db.session.get(Stage, stage_id)
    if stage is None or stage.project.teacher_id != current_user.id:
        abort(404)
    return stage


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "ProjectTracker"})


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if not email or not name or not password or role not in {"teacher", "student"}:
            flash("Заполните все поля и выберите корректную роль.")
            return render_template("register.html"), 400

        existing_user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()
        if existing_user is not None:
            flash("Пользователь с таким email уже существует.")
            return render_template("register.html"), 400

        user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("main.dashboard"))

    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()
        if user is None or not check_password_hash(user.password_hash, password):
            flash("Неверный email или пароль.")
            return render_template("login.html"), 400

        login_user(user)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@main_bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main_bp.get("/dashboard")
@login_required
def dashboard():
    if current_user.role == "teacher":
        return redirect(url_for("main.teacher_dashboard"))
    if current_user.role == "student":
        return redirect(url_for("main.student_dashboard"))
    abort(403)


@main_bp.get("/teacher")
@login_required
@role_required("teacher")
def teacher_dashboard():
    return redirect(url_for("main.teacher_projects"))


@main_bp.get("/student")
@login_required
@role_required("student")
def student_dashboard():
    return render_template("student_dashboard.html")


@main_bp.get("/teacher/projects")
@login_required
@role_required("teacher")
def teacher_projects():
    projects = db.session.execute(
        db.select(Project).filter_by(teacher_id=current_user.id).order_by(Project.created_at.desc())
    ).scalars()
    return render_template("teacher_projects.html", projects=projects)


@main_bp.route("/teacher/project/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def teacher_project_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not description:
            flash("Заполните название и описание проекта.")
            return render_template("teacher_project_form.html"), 400

        project = Project(
            title=title,
            description=description,
            teacher_id=current_user.id,
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for("main.teacher_project_detail", project_id=project.id))

    return render_template("teacher_project_form.html")


@main_bp.get("/teacher/project/<int:project_id>")
@login_required
@role_required("teacher")
def teacher_project_detail(project_id):
    project = get_teacher_project_or_404(project_id)
    return render_template("teacher_project_detail.html", project=project)


@main_bp.route("/teacher/stage/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def teacher_stage_new():
    project_id = request.args.get("project_id", type=int)
    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)

    if not project_id:
        abort(404)

    project = get_teacher_project_or_404(project_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        deadline_raw = request.form.get("deadline", "").strip()
        order_num = request.form.get("order_num", type=int)

        if not title or not description or not deadline_raw or order_num is None:
            flash("Заполните все поля этапа.")
            return render_template("teacher_stage_form.html", project=project, stage=None), 400

        try:
            deadline = datetime.strptime(deadline_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Некорректная дата дедлайна.")
            return render_template("teacher_stage_form.html", project=project, stage=None), 400

        stage = Stage(
            project_id=project.id,
            title=title,
            description=description,
            deadline=deadline,
            order_num=order_num,
        )
        db.session.add(stage)
        db.session.commit()
        return redirect(url_for("main.teacher_project_detail", project_id=project.id))

    return render_template("teacher_stage_form.html", project=project, stage=None)


@main_bp.route("/teacher/stage/<int:stage_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def teacher_stage_edit(stage_id):
    stage = get_teacher_stage_or_404(stage_id)
    project = stage.project

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        deadline_raw = request.form.get("deadline", "").strip()
        order_num = request.form.get("order_num", type=int)

        if not title or not description or not deadline_raw or order_num is None:
            flash("Заполните все поля этапа.")
            return render_template("teacher_stage_form.html", project=project, stage=stage), 400

        try:
            deadline = datetime.strptime(deadline_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Некорректная дата дедлайна.")
            return render_template("teacher_stage_form.html", project=project, stage=stage), 400

        stage.title = title
        stage.description = description
        stage.deadline = deadline
        stage.order_num = order_num
        db.session.commit()
        return redirect(url_for("main.teacher_project_detail", project_id=project.id))

    return render_template("teacher_stage_form.html", project=project, stage=stage)


@main_bp.get("/teacher/student/<int:student_id>")
@login_required
@role_required("teacher")
def teacher_student_detail(student_id):
    project_id = request.args.get("project_id", type=int)
    if not project_id:
        abort(404)

    project = get_teacher_project_or_404(project_id)
    student = db.session.get(User, student_id)
    if student is None or student.role != "student":
        abort(404)

    progress_entries = db.session.execute(
        db.select(Progress)
        .join(Stage)
        .filter(Progress.student_id == student.id, Stage.project_id == project.id)
        .order_by(Stage.order_num)
    ).scalars()

    return render_template(
        "teacher_student_detail.html",
        project=project,
        student=student,
        progress_entries=progress_entries,
    )
