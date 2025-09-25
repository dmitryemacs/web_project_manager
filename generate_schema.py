# generate_schema.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения, чтобы database.py мог подключиться к БД
load_dotenv()

# Импортируем Base из вашего файла database.py
# Base содержит метаданные всех ваших моделей SQLAlchemy
from database import Base

# Импортируем все ваши модели, чтобы они были зарегистрированы в Base.metadata
# Это важно, чтобы ERAlchemy2 мог их обнаружить
from models import (
    Role, Team, User, Project, Priority, Status, Task, Comment, Attachment
)

# Импортируем функцию для генерации ER-диаграммы
try:
    from eralchemy2 import render_er
except ImportError:
    print("Ошибка: Библиотека 'eralchemy2' не установлена.")
    print("Пожалуйста, установите ее командой: pip install eralchemy2")
    print("Также убедитесь, что Graphviz установлен в вашей системе.")
    exit(1)

def generate_er_diagram(output_file="database_schema.png"):
    """
    Генерирует ER-диаграмму из моделей SQLAlchemy.
    """
    print(f"Попытка сгенерировать ER-диаграмму в файл: {output_file}")
    try:
        # render_er принимает объект Base (или список моделей) и путь к выходному файлу
        # Он автоматически обнаруживает все модели, зарегистрированные в Base.metadata
        render_er(Base, output_file)
        print(f"ER-диаграмма успешно сгенерирована в {output_file}")
    except Exception as e:
        print(f"Произошла ошибка при генерации ER-диаграммы: {e}")
        print("Возможно, Graphviz не установлен или не добавлен в PATH.")
        print("Пожалуйста, проверьте установку Graphviz.")

if __name__ == "__main__":
    generate_er_diagram()
