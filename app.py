from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy.orm import scoped_session
from datetime import datetime
import os

from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt

from database import Base, engine, SessionLocal
from models import User, Team, Project, Task, Priority, Status, Role, Comment, Attachment
from crud import (
    create_initial_data, create_user, create_team, create_project, create_task,
    create_comment, create_attachment, get_users, get_teams, get_projects,
    get_projects_by_team, get_tasks_by_project, get_comments_for_task, get_attachments_for_task,
    get_roles, create_role, get_user_by_email, get_user_by_id, verify_password,
    get_project_by_id, get_task_by_id # Добавлено
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "files")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
login_manager.login_message_category = "warning"

bcrypt = Bcrypt(app)

Base.metadata.create_all(bind=engine)

db_session = scoped_session(SessionLocal)

with app.app_context():
    create_initial_data(db_session())

@app.teardown_appcontext
def remove_session(exception=None):
    db_session.remove()

@login_manager.user_loader
def load_user(user_id):
    db = db_session()
    return get_user_by_id(db, int(user_id))

@app.route("/")
@login_required
def dashboard():
    db = db_session()
    projects = get_projects(db) # Используем get_projects из crud
    tasks = db.query(Task).all() # Пока не будем жадно загружать для дашборда, чтобы не перегружать
    users = get_users(db)
    teams = get_teams(db)
    priorities = db.query(Priority).all()
    statuses = db.query(Status).all()

    stats = {
        "projects": len(projects),
        "tasks": len(tasks),
        "users": len(users),
        "teams": len(teams),
        "tasks_done": db.query(Task).filter(Task.is_completed == True).count(),
    }
    return render_template("index.html", projects=projects, tasks=tasks, users=users, teams=teams,
                           priorities=priorities, statuses=statuses, stats=stats, current_user=current_user)

# ---- Аутентификация ----
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        db = db_session()
        user = get_user_by_email(db, email)

        if user and verify_password(user.password, password):
            login_user(user)
            flash("Вы успешно вошли в систему.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        else:
            flash("Неверный email или пароль.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        db = db_session()
        if get_user_by_email(db, email):
            flash("Пользователь с таким email уже существует.", "danger")
            return redirect(url_for("register"))

        viewer_role = db.query(Role).filter_by(name="viewer").first()
        role_id = viewer_role.role_id if viewer_role else None

        create_user(db, first_name, last_name, email, password, role_id)
        flash("Регистрация прошла успешно! Теперь вы можете войти.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


# -------- Projects --------
@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    db = db_session()
    project = get_project_by_id(db, project_id) # Используем новую функцию
    if not project:
        flash("Проект не найден.", "danger")
        return redirect(url_for("dashboard"))

    # Задачи для этого проекта уже загружены через joinedload в get_project_by_id,
    # но для удобства передачи в шаблон можно использовать project.tasks
    # Если хотим отфильтровать или отсортировать, можно использовать get_tasks_by_project(db, project_id)
    tasks = get_tasks_by_project(db, project_id) # Используем эту функцию для получения задач с жадной загрузкой

    users = get_users(db) # Для выпадающего списка исполнителей в форме новой задачи
    priorities = db.query(Priority).all() # Для выпадающего списка приоритетов
    statuses = db.query(Status).all() # Для выпадающего списка статусов

    return render_template("project_detail.html",
                           project=project,
                           tasks=tasks,
                           users=users,
                           priorities=priorities,
                           statuses=statuses)

@app.post("/projects/add")
@login_required
def add_project():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    team_id = request.form.get("team_id") or None
    due_date_str = request.form.get("due_date") or None
    due_date = datetime.fromisoformat(due_date_str) if due_date_str else None
    db = db_session()
    p = create_project(db, name, description, int(team_id) if team_id else None, due_date)
    flash("Проект создан", "success")
    return redirect(url_for("project_detail", project_id=p.project_id)) # Перенаправляем на страницу проекта


# -------- Tasks --------
@app.route("/tasks/<int:task_id>")
@login_required
def task_detail(task_id):
    db = db_session()
    task = get_task_by_id(db, task_id) # Используем новую функцию
    if not task:
        flash("Задача не найдена.", "danger")
        return redirect(url_for("dashboard"))

    # Комментарии и вложения уже загружены через joinedload в get_task_by_id
    comments = task.comments
    attachments = task.attachments

    return render_template("task_detail.html",
                           task=task,
                           comments=comments,
                           attachments=attachments)

@app.post("/tasks/add")
@login_required
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    project_id = int(request.form.get("project_id"))
    assignee_id = request.form.get("assignee_id") or None
    priority_id = request.form.get("priority_id") or None
    status_id = request.form.get("status_id") or None
    due_date_str = request.form.get("due_date") or None
    due_date = datetime.fromisoformat(due_date_str) if due_date_str else None

    db = db_session()
    create_task(db, title, description, project_id,
                int(assignee_id) if assignee_id else None,
                int(priority_id) if priority_id else None,
                int(status_id) if status_id else None,
                due_date)
    flash("Задача создана", "success")
    # Перенаправляем на страницу проекта, из которого была добавлена задача
    return redirect(url_for("project_detail", project_id=project_id))

@app.post("/tasks/<int:task_id>/toggle")
@login_required
def toggle_task(task_id):
    db = db_session()
    t = db.query(Task).get(task_id)
    if t:
        t.is_completed = not t.is_completed
        db.commit()
        flash("Статус задачи обновлён", "info")
    # Перенаправляем на страницу задачи, если пришли оттуда, иначе на дашборд
    if request.referrer and f"/tasks/{task_id}" in request.referrer:
        return redirect(url_for("task_detail", task_id=task_id))
    return redirect(url_for("dashboard"))


# -------- Comments --------
@app.post("/comments/add")
@login_required
def add_comment():
    task_id = int(request.form.get("task_id"))
    user_id = current_user.user_id
    content = request.form.get("content", "").strip()
    db = db_session()
    create_comment(db, task_id, user_id, content)
    flash("Комментарий добавлен", "success")
    return redirect(url_for("task_detail", task_id=task_id)) # Перенаправляем на страницу задачи


# -------- Attachments --------
@app.post("/attachments/upload")
@login_required
def upload_attachment():
    task_id = int(request.form.get("task_id"))
    file = request.files.get("file")
    if not file or file.filename == '':
        flash("Файл не выбран", "warning")
        return redirect(url_for("task_detail", task_id=task_id)) # Перенаправляем на страницу задачи

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    db = db_session()
    create_attachment(db, task_id, save_path)
    flash("Файл загружен", "success")
    return redirect(url_for("task_detail", task_id=task_id)) # Перенаправляем на страницу задачи

@app.get("/files/<path:filename>")
@login_required
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


# -------- Reference data: Teams, Users, Roles --------
@app.post("/teams/add")
@login_required
def add_team():
    name = request.form.get("team_name", "").strip()
    db = db_session()
    team = create_team(db, name)
    flash("Команда создана", "success")
    return redirect(url_for("dashboard"))

@app.post("/users/add")
@login_required
def add_user_view():
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    role_id = request.form.get("role_id") or None
    db = db_session()

    if get_user_by_email(db, email):
        flash("Пользователь с таким email уже существует.", "danger")
        return redirect(url_for("dashboard"))

    user = create_user(db, first_name, last_name, email, password,
                int(role_id) if role_id else None)
    flash("Пользователь создан", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)