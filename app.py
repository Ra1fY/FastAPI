import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

# Загрузка CSS стилей
def load_css():
    """Загрузка CSS стилей из файла"""
    css_file = Path(__file__).parent / "styles.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning("Файл стилей не найден")

# Загрузка CSS
load_css()

# Конфигурация API
API_URL = "https://fastapi-jonsonsbaby.amvera.io/"

# Настройка страницы
st.set_page_config(
    page_title="Менеджер задач",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация сессии
if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None

def make_request(method, endpoint, **kwargs):
    """Универсальная функция для запросов к API"""
    headers = {"Content-Type": "application/json"}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    url = f"{API_URL}{endpoint}"
    
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        if response.status_code == 401:
            st.session_state.token = None
            st.session_state.username = None
            st.error("Сессия истекла. Пожалуйста, войдите снова.")
            return None
        return response
    except requests.exceptions.ConnectionError:
        st.error("Не удается подключиться к серверу. Убедитесь, что бэкенд запущен.")
        return None

def get_priority_style(priority):
    """Возвращает CSS класс для приоритета"""
    if priority >= 4:
        return "priority-high"
    elif priority >= 2:
        return "priority-medium"
    else:
        return "priority-low"

def get_priority_text(priority):
    """Возвращает текст приоритета"""
    if priority >= 4:
        return f"🔴 Высокий ({priority})"
    elif priority >= 2:
        return f"🟡 Средний ({priority})"
    else:
        return f"🟢 Низкий ({priority})"

def get_status_class(status):
    """Возвращает CSS класс для статуса"""
    return f"status-badge status-{status.replace('_', '-')}"

def get_status_text(status):
    """Возвращает текст статуса"""
    statuses = {
        "pending": "⏳ В ожидании",
        "in_progress": "🔄 В работе",
        "completed": "✅ Завершено"
    }
    return statuses.get(status, status)

def login_page():
    """Страница входа с улучшенным дизайном"""
    st.markdown("""
    <div class="main-header">
        <h1>📝 Менеджер задач</h1>
        <p>Управляйте своими задачами эффективно и организованно</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # st.markdown('<div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Вход", "📝 Регистрация"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Имя пользователя", placeholder="Введите ваше имя")
                password = st.text_input("Пароль", type="password", placeholder="Введите пароль")
                submit = st.form_submit_button("Войти", use_container_width=True)
                
                if submit:
                    if username and password:
                        response = make_request(
                            "POST", 
                            "/api/token",
                            data={"username": username, "password": password}
                        )
                        
                        if response and response.status_code == 200:
                            data = response.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("❌ Неверное имя пользователя или пароль")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Имя пользователя", placeholder="Придумайте имя")
                email = st.text_input("Email", placeholder="your@email.com")
                new_password = st.text_input("Пароль", type="password", placeholder="Минимум 6 символов")
                confirm_password = st.text_input("Подтвердите пароль", type="password")
                submit_reg = st.form_submit_button("Зарегистрироваться", use_container_width=True)
                
                if submit_reg:
                    if new_password != confirm_password:
                        st.error("❌ Пароли не совпадают")
                    elif len(new_password) < 6:
                        st.error("❌ Пароль должен содержать минимум 6 символов")
                    else:
                        response = make_request(
                            "POST",
                            "/api/register",
                            json={
                                "username": new_username,
                                "email": email,
                                "password": new_password
                            }
                        )
                        
                        if response and response.status_code == 200:
                            st.success("✅ Регистрация успешна! Теперь войдите в систему.")
                        else:
                            st.error("❌ Ошибка регистрации. Возможно, имя пользователя уже занято.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    """Основное приложение"""
    # Боковая панель с информацией о пользователе
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-user">
            <h3>👋 Привет, {st.session_state.username}!</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.rerun()
        
        st.divider()
        
        # Навигация
        page = st.radio(
            "📋 Навигация",
            ["🏠 Главная", "📋 Мои задачи", "➕ Создать задачу", "📊 Статистика"],
            format_func=lambda x: x
        )
        
        # Информация о версии
        st.divider()
        st.caption("Версия 1.0.0 | Сделано с ❤️")
    
    # Отображение выбранной страницы
    if page == "🏠 Главная":
        show_dashboard()
    elif page == "📋 Мои задачи":
        show_tasks_list()
    elif page == "➕ Создать задачу":
        show_create_task()
    elif page == "📊 Статистика":
        show_statistics()

def show_dashboard():
    """Дашборд с красивыми карточками"""
    st.markdown('<div class="main-header"><h1>📊 Панель управления</h1><p>Обзор ваших задач и прогресса</p></div>', unsafe_allow_html=True)
    
    # Получаем задачи
    response = make_request("GET", "/api/tasks")
    
    if response and response.status_code == 200:
        tasks = response.json()
        
        if not tasks:
            st.info("✨ У вас пока нет задач. Создайте свою первую задачу!")
            if st.button("➕ Создать задачу", use_container_width=True):
                st.session_state.current_page = "➕ Создать задачу"
                st.rerun()
            return
        
        # Статистика в карточках
        col1, col2, col3, col4 = st.columns(4)
        
        total = len(tasks)
        completed = len([t for t in tasks if t["status"] == "completed"])
        in_progress = len([t for t in tasks if t["status"] == "in_progress"])
        high_priority = len([t for t in tasks if t["priority"] >= 4])
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">📌 Всего задач</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{completed}</div>
                <div class="stat-label">✅ Завершено</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{in_progress}</div>
                <div class="stat-label">🔄 В работе</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{high_priority}</div>
                <div class="stat-label">🔴 Высокий приоритет</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Графики
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h3 style='text-align: center;'>📈 Распределение по статусам</h3>", unsafe_allow_html=True)
            status_counts = {
                "В ожидании": len([t for t in tasks if t["status"] == "pending"]),
                "В работе": len([t for t in tasks if t["status"] == "in_progress"]),
                "Завершено": len([t for t in tasks if t["status"] == "completed"])
            }
            
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                color_discrete_sequence=["#ffc107", "#17a2b8", "#28a745"],
                hole=0.3
            )
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("<h3 style='text-align: center;'>🎯 Распределение по приоритетам</h3>", unsafe_allow_html=True)
            priority_counts = {
                "Высокий (4-5)": len([t for t in tasks if t["priority"] >= 4]),
                "Средний (2-3)": len([t for t in tasks if 2 <= t["priority"] <= 3]),
                "Низкий (1)": len([t for t in tasks if t["priority"] == 1])
            }
            
            fig = px.bar(
                x=list(priority_counts.keys()),
                y=list(priority_counts.values()),
                color=list(priority_counts.keys()),
                color_discrete_sequence=["#dc3545", "#ffc107", "#28a745"],
                text_auto=True
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Последние задачи
        st.markdown("<h3 style='margin-top: 2rem;'>📝 Последние задачи</h3>", unsafe_allow_html=True)
        recent_tasks = sorted(tasks, key=lambda x: x["created_at"], reverse=True)[:5]
        
        for task in recent_tasks:
            priority_class = get_priority_style(task["priority"])
            status_class = get_status_class(task["status"])
            
            st.markdown(f"""
            <div class="task-card">
                <h4>📌 {task['title']}</h4>
                <p>{task.get('description', 'Нет описания')[:100]}</p>
                <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                    <span class="{status_class}">{get_status_text(task['status'])}</span>
                    <span class="{priority_class}">{get_priority_text(task['priority'])}</span>
                    <span style="color: #6c757d;">📅 {task['created_at'][:19]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_tasks_list():
    """Список задач с фильтрацией"""
    st.markdown('<div class="main-header"><h1>📋 Мои задачи</h1><p>Управляйте и отслеживайте свои задачи</p></div>', unsafe_allow_html=True)
    
    # Фильтры
    with st.expander("🔍 Фильтры и сортировка", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sort_by = st.selectbox(
                "Сортировать по",
                ["created_at", "priority", "title", "status"],
                format_func=lambda x: {
                    "created_at": "Дате создания",
                    "priority": "Приоритету",
                    "title": "Названию",
                    "status": "Статусу"
                }[x]
            )
        
        with col2:
            order = st.selectbox(
                "Порядок",
                ["desc", "asc"],
                format_func=lambda x: "По убыванию" if x == "desc" else "По возрастанию"
            )
        
        with col3:
            priority_filter = st.selectbox(
                "Приоритет",
                ["Все", "Высокий (4-5)", "Средний (2-3)", "Низкий (1)"]
            )
        
        with col4:
            top_n = st.number_input("Топ задач", min_value=0, max_value=50, value=0, step=5)
        
        search = st.text_input("🔍 Поиск", placeholder="Введите текст для поиска в названии или описании...")
    
    # Получаем задачи
    params = {"sort_by": sort_by, "order": order}
    if search:
        params["search"] = search
    if top_n > 0:
        params["top_n"] = top_n
    
    response = make_request("GET", "/api/tasks", params=params)
    
    if response and response.status_code == 200:
        tasks = response.json()
        
        # Применяем фильтр по приоритету
        if priority_filter != "Все":
            if priority_filter == "Высокий (4-5)":
                tasks = [t for t in tasks if t["priority"] >= 4]
            elif priority_filter == "Средний (2-3)":
                tasks = [t for t in tasks if 2 <= t["priority"] <= 3]
            else:
                tasks = [t for t in tasks if t["priority"] == 1]
        
        if not tasks:
            st.info("🔍 Задачи не найдены")
            return
        
        # Отображаем задачи
        st.markdown(f"### Найдено задач: {len(tasks)}")
        
        for task in tasks:
            priority_class = get_priority_style(task["priority"])
            status_class = get_status_class(task["status"])
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])
                
                with col1:
                    st.markdown(f"**📌 {task['title']}**")
                    if task.get('description'):
                        st.caption(task['description'][:100])
                
                with col2:
                    st.markdown(f'<span class="{status_class}">{get_status_text(task["status"])}</span>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f'<span class="{priority_class}">{get_priority_text(task["priority"])}</span>', unsafe_allow_html=True)
                
                with col4:
                    if st.button(f"✏️", key=f"edit_{task['id']}", help="Редактировать"):
                        show_edit_task(task)
                    if st.button(f"🗑️", key=f"delete_{task['id']}", help="Удалить"):
                        delete_response = make_request("DELETE", f"/api/tasks/{task['id']}")
                        if delete_response and delete_response.status_code == 200:
                            st.success("✅ Задача удалена")
                            st.rerun()
                
                st.divider()

def show_create_task():
    """Создание задачи"""
    st.markdown('<div class="main-header"><h1>➕ Создать новую задачу</h1><p>Добавьте новую задачу в ваш список</p></div>', unsafe_allow_html=True)
    
    with st.form("create_task_form", clear_on_submit=True):
        title = st.text_input("Название задачи*", max_chars=200, placeholder="Введите название задачи")
        description = st.text_area("Описание", height=100, placeholder="Подробное описание задачи...")
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox(
                "Статус",
                ["pending", "in_progress", "completed"],
                format_func=lambda x: get_status_text(x)
            )
        with col2:
            priority = st.slider("Приоритет", 1, 5, 3, help="1 - низкий, 5 - высокий")
        
        submitted = st.form_submit_button("✅ Создать задачу", use_container_width=True)
        
        if submitted:
            if not title:
                st.error("❌ Название задачи обязательно")
            else:
                task_data = {
                    "title": title,
                    "description": description if description else None,
                    "status": status,
                    "priority": priority
                }
                response = make_request("POST", "/api/tasks", json=task_data)
                
                if response and response.status_code == 200:
                    st.success("✅ Задача успешно создана!")
                    st.balloons()
                else:
                    st.error("❌ Ошибка при создании задачи")

def show_statistics():
    """Статистика"""
    st.markdown('<div class="main-header"><h1>📊 Статистика</h1><p>Анализ вашей продуктивности</p></div>', unsafe_allow_html=True)
    
    response = make_request("GET", "/api/statistics")
    
    if response and response.status_code == 200:
        stats = response.json()
        
        # Общая статистика
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total']}</div>
                <div class="stat-label">Всего задач</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{completion_rate:.1f}%</div>
                <div class="stat-label">Выполнено</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['avg_priority']:.1f}</div>
                <div class="stat-label">Средний приоритет</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Детальная статистика
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 По статусам")
            status_data = {
                "В ожидании": stats['pending'],
                "В работе": stats['in_progress'],
                "Завершено": stats['completed']
            }
            fig = px.pie(values=list(status_data.values()), names=list(status_data.keys()), hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🎯 Рекомендации")
            if stats['high_priority'] > stats['total'] * 0.5:
                st.warning("⚠️ У вас много задач с высоким приоритетом. Сосредоточьтесь на них в первую очередь!")
            elif stats['completed'] / stats['total'] > 0.7:
                st.success("🎉 Отличная продуктивность! Продолжайте в том же духе!")
            elif stats['in_progress'] > stats['total'] * 0.3:
                st.info("💡 У вас много задач в работе. Попробуйте завершить некоторые из них.")
            else:
                st.success("👍 Хороший баланс задач! Держите ритм!")
        
        # Прогресс-бар
        st.markdown("### 📈 Прогресс выполнения")
        completion_percentage = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        st.progress(completion_percentage / 100)
        st.caption(f"Выполнено {stats['completed']} из {stats['total']} задач ({completion_percentage:.1f}%)")

def show_edit_task(task):
    """Диалог редактирования задачи"""
    with st.form(f"edit_task_form_{task['id']}"):
        st.subheader(f"✏️ Редактирование: {task['title']}")
        
        title = st.text_input("Название", value=task['title'])
        description = st.text_area("Описание", value=task.get('description', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox(
                "Статус",
                ["pending", "in_progress", "completed"],
                index=["pending", "in_progress", "completed"].index(task['status']),
                format_func=lambda x: get_status_text(x)
            )
        with col2:
            priority = st.slider("Приоритет", 1, 5, value=task['priority'])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Сохранить", use_container_width=True):
                update_data = {
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority
                }
                response = make_request("PUT", f"/api/tasks/{task['id']}", json=update_data)
                if response and response.status_code == 200:
                    st.success("✅ Задача обновлена")
                    st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Отмена", use_container_width=True):
                st.rerun()

# Запуск приложения
if st.session_state.token and st.session_state.username:
    main_app()
else:
    login_page()
