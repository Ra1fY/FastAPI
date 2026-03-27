from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from database import get_db, init_db
from models import User, Task, TaskStatus
from schemas import (
    TaskCreate, TaskUpdate, TaskResponse, 
    UserCreate, UserResponse, Token
)
from crud import (
    create_task, get_user_tasks, get_task_by_id, 
    update_task, delete_task, search_tasks,
    create_user, get_user_by_username, authenticate_user
)
from auth import create_access_token, verify_token

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск: инициализируем базу данных
    init_db()
    print("✅ База данных SQLite инициализирована")
    print("🚀 FastAPI приложение запущено")
    yield
    # Завершение: закрываем соединения при необходимости
    print("👋 FastAPI приложение остановлено")

app = FastAPI(
    title="Менеджер задач API",
    description="API для управления задачами с SQLite и JWT аутентификацией",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS для Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Получение текущего пользователя по JWT токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = verify_token(token)
    if username is None:
        raise credentials_exception
    
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    
    return user

# ============= АУТЕНТИФИКАЦИЯ =============

@app.post("/api/register", response_model=UserResponse, tags=["Аутентификация"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверяем существование пользователя
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    # Проверяем email
    from crud import get_user_by_email
    db_email = get_user_by_email(db, user.email)
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    return create_user(db, user)

@app.post("/api/token", response_model=Token, tags=["Аутентификация"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Вход в систему и получение JWT токена"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ============= ОПЕРАЦИИ С ЗАДАЧАМИ =============

@app.post("/api/tasks", response_model=TaskResponse, tags=["Задачи"])
def create_task_endpoint(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание новой задачи"""
    return create_task(db, task, current_user.id)

@app.get("/api/tasks", response_model=List[TaskResponse], tags=["Задачи"])
def list_tasks(
    sort_by: Optional[str] = Query(None, regex="^(title|status|created_at|priority)$"),
    order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
    search: Optional[str] = None,
    priority_filter: Optional[int] = Query(None, ge=1, le=5),
    top_n: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка задач с возможностью:
    - Сортировки по заголовку, статусу, дате или приоритету
    - Поиска по тексту
    - Фильтрации по приоритету
    - Получения топ-N приоритетных задач
    """
    tasks = get_user_tasks(db, current_user.id)
    
    # Поиск
    if search:
        tasks = search_tasks(tasks, search)
    
    # Фильтр по приоритету
    if priority_filter:
        tasks = [t for t in tasks if t.priority == priority_filter]
    
    # Сортировка
    if sort_by:
        reverse = order == "desc"
        if sort_by == "title":
            tasks.sort(key=lambda x: x.title, reverse=reverse)
        elif sort_by == "status":
            tasks.sort(key=lambda x: x.status.value, reverse=reverse)
        elif sort_by == "created_at":
            tasks.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == "priority":
            tasks.sort(key=lambda x: x.priority, reverse=reverse)
    
    # Топ-N приоритетных
    if top_n:
        tasks.sort(key=lambda x: x.priority, reverse=True)
        tasks = tasks[:top_n]
    
    return tasks

@app.get("/api/tasks/{task_id}", response_model=TaskResponse, tags=["Задачи"])
def get_task_endpoint(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение конкретной задачи"""
    task = get_task_by_id(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    return task

@app.put("/api/tasks/{task_id}", response_model=TaskResponse, tags=["Задачи"])
def update_task_endpoint(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление задачи"""
    task = get_task_by_id(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    return update_task(db, task_id, task_update)

@app.delete("/api/tasks/{task_id}", tags=["Задачи"])
def delete_task_endpoint(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление задачи"""
    task = get_task_by_id(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    delete_task(db, task_id)
    return {"message": "Задача успешно удалена"}

@app.get("/api/statistics", tags=["Статистика"])
def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики по задачам пользователя"""
    tasks = get_user_tasks(db, current_user.id)
    
    stats = {
        "total": len(tasks),
        "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
        "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
        "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
        "avg_priority": sum(t.priority for t in tasks) / len(tasks) if tasks else 0,
        "high_priority": len([t for t in tasks if t.priority >= 4]),
    }
    return stats

@app.get("/api/health", tags=["Система"])
def health_check():
    """Проверка работоспособности"""
    return {
        "status": "ok",
        "database": "sqlite",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/user/me", response_model=UserResponse, tags=["Аутентификация"])
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Получение информации о текущем пользователе"""
    return current_user