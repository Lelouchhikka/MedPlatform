## 📥 Установка
1. **Склонируйте репозиторий:**
   ```bash
   git clone https://github.com/<ВАШ_ЛОГИН>/MedPlatforma.git
   cd MedPlatforma
   ```

2. **Создайте и активируйте виртуальную среду Python:**
   - Для Windows:
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - Для Mac/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Установите зависимости проекта:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Примените миграции базы данных:**
   ```bash
   python manage.py migrate
   ```

5. **Запустите сидер (опционально):**
   Если необходимо загрузить тестовые данные в базу, можно использовать следующий инструмент:
   ```bash
   python -m core.seeder
   ```


6. **Запустите локальный сервер разработки:**
   ```bash
   python manage.py runserver
   ```

Теперь проект доступен по адресу http://127.0.0.1:8000.