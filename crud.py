from sqlalchemy.orm import Session, joinedload # Добавлено joinedload
from datetime import datetime
from models import User, Team, Project, Task, Priority, Status, Role, Comment, Attachment
from flask_bcrypt import generate_password_hash, check_password_hash

# Добавлено: Функции для работы с паролями
def hash_password(password: str) -> str:
    return generate_password_hash(password).decode('utf-8')

def verify_password(hashed_password: str, password: str) -> bool:
    return check_password_hash(hashed_password, password)

def create_initial_data(db: Session):
    # Roles
    default_roles = ["admin", "manager", "developer", "viewer"]
    for r in default_roles:
        if not db.query(Role).filter_by(name=r).first():
            db.add(Role(name=r))
    db.commit() # Коммит ролей, чтобы они были доступны для создания пользователя

    # Teams
    if not db.query(Team).first():
        db.add_all([Team(name="Core"), Team(name="Mobile")])

    # Priorities
    for p in ["Low", "Medium", "High", "Critical"]:
        if not db.query(Priority).filter_by(name=p).first():
            db.add(Priority(name=p))

    # Statuses
    for s in ["Backlog", "In Progress", "In Review", "Done"]:
        if not db.query(Status).filter_by(name=s).first():
            db.add(Status(name=s))

    db.commit()

    # Создание начального пользователя (админа)
    if not db.query(User).filter_by(email="admin@example.com").first():
        admin_role = db.query(Role).filter_by(name="admin").first()
        if admin_role:
            create_user(db, "Admin", "User", "admin@example.com", "admin_password", admin_role.role_id)
            print("Создан пользователь Admin с email: admin@example.com и паролем: admin_password")

    # Создание роли "viewer", если ее нет (для новых регистраций)
    if not db.query(Role).filter_by(name="viewer").first():
        db.add(Role(name="viewer"))
        db.commit()


# ---- Users ----
def create_user(db: Session, first_name: str, last_name: str, email: str, password: str, role_id: int | None = None):
    hashed_password = hash_password(password)
    user = User(first_name=first_name, last_name=last_name, email=email, password=hashed_password, role_id=role_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session):
    return db.query(User).all()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).get(user_id) # Используем get() для получения по первичному ключу


# ---- Teams ----
def create_team(db: Session, name: str):
    team = Team(name=name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

def get_teams(db: Session):
    return db.query(Team).all()


# ---- Projects ----
def create_project(db: Session, name: str, description: str | None, team_id: int | None, due_date: datetime | None):
    project = Project(name=name, description=description, team_id=team_id, due_date=due_date)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get_projects(db: Session):
    return db.query(Project).all()

# Добавлено: Получение проекта по ID с жадной загрузкой команды и задач
def get_project_by_id(db: Session, project_id: int):
    return db.query(Project).options(joinedload(Project.team), joinedload(Project.tasks)).get(project_id)

def get_projects_by_team(db: Session, team_id: int):
    return db.query(Project).filter(Project.team_id == team_id).all()


# ---- Tasks ----
def create_task(db: Session, title: str, description: str | None, project_id: int, assignee_id: int | None, priority_id: int | None, status_id: int | None, due_date: datetime | None):
    task = Task(title=title, description=description, project_id=project_id,
                assignee_id=assignee_id, priority_id=priority_id, status_id=status_id, due_date=due_date)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_tasks_by_project(db: Session, project_id: int):
    # Добавлено: Жадная загрузка связанных сущностей для отображения в таблице задач
    return db.query(Task).filter(Task.project_id == project_id).options(
        joinedload(Task.assignee),
        joinedload(Task.priority),
        joinedload(Task.status)
    ).all()

# Добавлено: Получение задачи по ID с жадной загрузкой всех связанных сущностей
def get_task_by_id(db: Session, task_id: int):
    return db.query(Task).options(
        joinedload(Task.project),
        joinedload(Task.assignee),
        joinedload(Task.priority),
        joinedload(Task.status),
        joinedload(Task.comments).joinedload(Comment.user), # Загружаем комментарии и их пользователей
        joinedload(Task.attachments) # Загружаем вложения
    ).get(task_id)


# ---- Roles ----
def create_role(db: Session, name: str):
    role = Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def get_roles(db: Session):
    return db.query(Role).all()


# ---- Comments ----
def create_comment(db: Session, task_id: int, user_id: int, content: str):
    comment = Comment(task_id=task_id, user_id=user_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def get_comments_for_task(db: Session, task_id: int):
    # Добавлено: Жадная загрузка пользователя, оставившего комментарий
    return db.query(Comment).filter(Comment.task_id == task_id).options(joinedload(Comment.user)).order_by(Comment.created_at.asc()).all()


# ---- Attachments ----
def create_attachment(db: Session, task_id: int, file_path: str):
    att = Attachment(task_id=task_id, file_path=file_path)
    db.add(att)
    db.commit()
    db.refresh(att)
    return att

def get_attachments_for_task(db: Session, task_id: int):
    return db.query(Attachment).filter(Attachment.task_id == task_id).all()