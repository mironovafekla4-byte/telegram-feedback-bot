# Инструкция по развертыванию бота

## Локальный запуск

### Windows

1. Установите Python 3.7+ с [python.org](https://www.python.org/downloads/)
2. Откройте командную строку в папке проекта
3. Установите зависимости:
   ```cmd
   pip install -r requirements.txt
   ```
4. Настройте `service_account.json` согласно инструкции
5. Запустите бота:
   ```cmd
   python run_bot_simple.py
   ```

### Linux/macOS

1. Установите Python 3.7+
2. Откройте терминал в папке проекта
3. Создайте виртуальное окружение (рекомендуется):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
5. Настройте `service_account.json` согласно инструкции
6. Запустите бота:
   ```bash
   python3 run_bot_simple.py
   ```

## Развертывание на сервере

### Вариант 1: VPS/Dedicated Server

1. Подключитесь к серверу по SSH
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/telegram-feedback-bot.git
   cd telegram-feedback-bot
   ```
3. Установите зависимости:
   ```bash
   pip3 install -r requirements.txt
   ```
4. Загрузите `service_account.json` на сервер
5. Запустите бота в фоновом режиме с помощью screen или tmux:
   ```bash
   screen -S feedback-bot
   python3 run_bot_simple.py
   # Нажмите Ctrl+A, затем D для выхода из screen
   ```

### Вариант 2: Systemd Service (Linux)

1. Создайте файл службы:
   ```bash
   sudo nano /etc/systemd/system/feedback-bot.service
   ```

2. Вставьте следующий контент:
   ```ini
   [Unit]
   Description=Telegram Feedback Bot
   After=network.target

   [Service]
   Type=simple
   User=yourusername
   WorkingDirectory=/path/to/telegram-feedback-bot
   ExecStart=/usr/bin/python3 /path/to/telegram-feedback-bot/run_bot_simple.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Активируйте службу:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable feedback-bot
   sudo systemctl start feedback-bot
   ```

4. Проверьте статус:
   ```bash
   sudo systemctl status feedback-bot
   ```

### Вариант 3: Docker

1. Создайте `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["python", "run_bot_simple.py"]
   ```

2. Создайте `.dockerignore`:
   ```
   __pycache__
   *.pyc
   .git
   .gitignore
   README.md
   venv/
   ```

3. Соберите образ:
   ```bash
   docker build -t feedback-bot .
   ```

4. Запустите контейнер:
   ```bash
   docker run -d --name feedback-bot \
     -v $(pwd)/service_account.json:/app/service_account.json:ro \
     --restart unless-stopped \
     feedback-bot
   ```

### Вариант 4: Heroku

1. Создайте `Procfile`:
   ```
   worker: python run_bot_simple.py
   ```

2. Создайте `runtime.txt`:
   ```
   python-3.11.0
   ```

3. Инициализируйте Git и Heroku:
   ```bash
   git init
   heroku create your-bot-name
   ```

4. Установите переменные окружения:
   ```bash
   heroku config:set BOT_TOKEN=your_bot_token
   ```

5. Загрузите `service_account.json` как переменную окружения:
   ```bash
   heroku config:set GOOGLE_CREDENTIALS="$(cat service_account.json)"
   ```

6. Деплой:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

7. Запустите worker:
   ```bash
   heroku ps:scale worker=1
   ```

## Мониторинг

### Просмотр логов

**Screen:**
```bash
screen -r feedback-bot
```

**Systemd:**
```bash
sudo journalctl -u feedback-bot -f
```

**Docker:**
```bash
docker logs -f feedback-bot
```

**Heroku:**
```bash
heroku logs --tail
```

## Обновление бота

### Git
```bash
cd telegram-feedback-bot
git pull
sudo systemctl restart feedback-bot  # если используется systemd
```

### Docker
```bash
docker stop feedback-bot
docker rm feedback-bot
docker build -t feedback-bot .
docker run -d --name feedback-bot ... # команда запуска
```

## Безопасность

1. Никогда не коммитьте `service_account.json` и токены
2. Используйте переменные окружения для секретов
3. Регулярно обновляйте зависимости:
   ```bash
   pip install --upgrade -r requirements.txt
   ```
4. Настройте файрвол на сервере
5. Используйте HTTPS для всех API запросов

## Резервное копирование

1. Регулярно делайте бэкап Google Sheets
2. Сохраняйте копии `service_account.json` в безопасном месте
3. Бэкапьте файл `feedback.xlsx` (если используется)

## Решение проблем

**Бот не отвечает:**
- Проверьте логи
- Убедитесь, что сервис запущен
- Проверьте интернет-соединение

**Ошибки Google Sheets:**
- Проверьте права доступа service account
- Убедитесь, что API включен
- Проверьте ID таблицы

**Высокая нагрузка:**
- Увеличьте `timeout` в polling
- Используйте webhook вместо polling
- Масштабируйте сервер

## Поддержка

При возникновении проблем:
1. Проверьте документацию
2. Изучите Issues на GitHub
3. Создайте новый Issue с подробным описанием проблемы
