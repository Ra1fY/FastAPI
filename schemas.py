from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class TaskStatusEnum(str, Enum):
    """Статусы задач"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

# ============= СХЕМЫ ДЛЯ ЗАДАЧ =============

class TaskBase(BaseModel):
    """Базовая схема задачи"""
    title: str = Field(..., min_length=1, max_length=200, description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    status: TaskStatusEnum = Field(TaskStatusEnum.PENDING, description="Статус задачи")
    priority: int = Field(3, ge=1, le=5, description="Приоритет (1 - низкий, 5 - высокий)")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Валидация названия задачи"""
        if not v or not v.strip():
            raise ValueError('Название задачи не может быть пустым')
        return v.strip()
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Валидация приоритета"""
        if v < 1 or v > 5:
            raise ValueError('Приоритет должен быть от 1 до 5')
        return v

class TaskCreate(TaskBase):
    """Схема для создания задачи"""
    pass

class TaskUpdate(BaseModel):
    """Схема для обновления задачи (все поля опциональны)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    status: Optional[TaskStatusEnum] = Field(None, description="Статус задачи")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Приоритет (1-5)")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Название задачи не может быть пустым')
        return v.strip() if v else v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Приоритет должен быть от 1 до 5')
        return v

class TaskResponse(TaskBase):
    """Схема для ответа с задачей"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: int
    
    class Config:
        from_attributes = True  # Для SQLAlchemy моделей

# ============= СХЕМЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ =============

class UserBase(BaseModel):
    """Базовая схема пользователя"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Валидация имени пользователя"""
        if not v or not v.strip():
            raise ValueError('Имя пользователя не может быть пустым')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Имя пользователя может содержать только буквы, цифры, _ и -')
        return v.lower().strip()

class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str = Field(..., min_length=6, description="Пароль")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Валидация пароля"""
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v

class UserResponse(UserBase):
    """Схема для ответа с пользователем"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= СХЕМЫ ДЛЯ АУТЕНТИФИКАЦИИ =============

class Token(BaseModel):
    """Схема для JWT токена"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Схема для данных в токене"""
    username: Optional[str] = None

# ============= СХЕМЫ ДЛЯ СТАТИСТИКИ =============

class StatisticsResponse(BaseModel):
    """Схема для статистики"""
    total: int = Field(..., description="Всего задач")
    pending: int = Field(..., description="В ожидании")
    in_progress: int = Field(..., description="В работе")
    completed: int = Field(..., description="Завершено")
    avg_priority: float = Field(..., description="Средний приоритет")
    high_priority: int = Field(..., description="Задач с высоким приоритетом")
    
    class Config:
        from_attributes = True

# ============= СХЕМЫ ДЛЯ ОШИБОК =============

class ErrorResponse(BaseModel):
    """Схема для ответа с ошибкой"""
    detail: str = Field(..., description="Описание ошибки")
    status_code: Optional[int] = Field(None, description="Код ошибки")