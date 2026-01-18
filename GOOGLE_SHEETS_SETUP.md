# Инструкция по настройке Google Sheets

Для работы бота с Google Таблицей необходимо настроить сервисный аккаунт.

## Шаги настройки:

### 1. Создайте проект в Google Cloud Console
- Перейдите на https://console.cloud.google.com/
- Создайте новый проект или выберите существующий

### 2. Включите Google Sheets API
- Перейдите в: **APIs & Services** > **Library**
- Найдите "Google Sheets API"
- Нажмите **Enable**

### 3. Создайте сервисный аккаунт
- Перейдите в: **APIs & Services** > **Credentials**
- Нажмите **Create Credentials** > **Service Account**
- Введите имя (например: "feedback-bot-service")
- Нажмите **Create and Continue**
- Выберите роль: **Editor** (или **Owner**)
- Нажмите **Done**

### 4. Создайте ключ для сервисного аккаунта
- В списке сервисных аккаунтов найдите созданный аккаунт
- Нажмите на него
- Перейдите на вкладку **Keys**
- Нажмите **Add Key** > **Create new key**
- Выберите формат **JSON**
- Нажмите **Create**
- JSON файл автоматически скачается

### 5. Настройте файл в проекте
- Переименуйте скачанный JSON файл в `service_account.json`
- Поместите файл в папку проекта: `Projects/feedback_bot/service_account.json`

### 6. Предоставьте доступ к Google Таблице
- Откройте файл `service_account.json`
- Найдите поле `client_email` (например: `feedback-bot-service@your-project.iam.gserviceaccount.com`)
- Откройте вашу Google Таблицу по ссылке: https://docs.google.com/spreadsheets/d/1fwB_P5s3hFddejrcmheG6C6dPE8TG7N3iQx5D6fPUzI/edit
- Нажмите кнопку **Share** (Поделиться)
- Вставьте email из `client_email`
- Выберите права доступа: **Editor** (Редактор)
- Нажмите **Send**

### 7. Проверьте название листа
- Убедитесь, что лист в Google Таблице называется `Лист1`
- Если название другое, измените переменную `SHEET_NAME` в файле `run_bot_simple.py`

## Готово!

После настройки:
1. Перезапустите бота
2. Бот автоматически подключится к Google Таблице
3. Все данные будут сохраняться в Google Таблицу вместо локального Excel файла

## Структура данных в таблице

Таблица будет содержать 3 столбца:
- **Категория** (category) - категория вопроса без эмодзи
- **Вопрос** (question) - текст вопроса
- **Время** (time) - дата и время в формате YYYY-MM-DD HH:MM:SS

## Важно!

- Файл `service_account.json` содержит секретные ключи - **НЕ делитесь им публично!**
- Не коммитьте этот файл в Git (добавьте в .gitignore)
- Храните файл в безопасности
