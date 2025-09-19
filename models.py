from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from flask_login import UserMixin # Добавлено

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="role")

class Team(Base):
    __tablename__ = "teams"
    team_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    projects = relationship("Project", back_populates="team")

# Изменено: User наследует UserMixin
class User(Base, UserMixin): # Изменено
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=True)

    role = relationship("Role", back_populates="users")
    tasks = relationship("Task", back_populates="assignee")
    comments = relationship("Comment", back_populates="user")

    # Методы, требуемые Flask-Login
    def get_id(self):
        return str(self.user_id) # Flask-Login требует строковое представление ID

    def is_active(self):
        return True # Предполагаем, что все пользователи активны

    def is_authenticated(self):
        return True # Пользователь аутентифицирован, если вошел в систему

    def is_anonymous(self):
        return False # Пользователь не анонимен, если вошел в систему


class Project(Base):
    __tablename__ = "projects"
    project_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=True)
    due_date = Column(DateTime, nullable=True)

    team = relationship("Team", back_populates="projects")
    tasks = relationship("Task", back_populates="project")

class Priority(Base):
    __tablename__ = "priorities"
    priority_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    tasks = relationship("Task", back_populates="priority")

class Status(Base):
    __tablename__ = "statuses"
    status_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    tasks = relationship("Task", back_populates="status")

class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    priority_id = Column(Integer, ForeignKey("priorities.priority_id"), nullable=True)
    status_id = Column(Integer, ForeignKey("statuses.status_id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
    priority = relationship("Priority", back_populates="tasks")
    status = relationship("Status", back_populates="tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="task", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    comment_id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")

class Attachment(Base):
    __tablename__ = "attachments"
    attachment_id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="attachments")