from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib
from models import User, Task, TaskStatus
from schemas import UserCreate, TaskCreate, TaskUpdate

# Хэширование пароля
def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

# Пользователи
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Получение пользователя по email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Задачи
def create_task(db: Session, task: TaskCreate, user_id: int) -> Task:
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        user_id=user_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_user_tasks(db: Session, user_id: int) -> List[Task]:
    return db.query(Task).filter(Task.user_id == user_id).all()

def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()

def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Task:
    db_task = get_task_by_id(db, task_id)
    update_data = task_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = get_task_by_id(db, task_id)
    db.delete(db_task)
    db.commit()

def search_tasks(tasks: List[Task], search_term: str) -> List[Task]:
    """Поиск задач по заголовку и описанию"""
    search_lower = search_term.lower()
    return [
        task for task in tasks
        if search_lower in task.title.lower() 
        or (task.description and search_lower in task.description.lower())
    ]