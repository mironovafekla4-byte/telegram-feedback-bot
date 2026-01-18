@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Скрипт подготовки проекта к публикации на GitHub (Windows)

echo ==========================================
echo Подготовка проекта к публикации на GitHub
echo ==========================================
echo.

:: Проверка наличия Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [✗] Git не установлен
    echo Установите Git: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo [✓] Git установлен
echo.

:: Проверка на наличие секретных файлов
echo Проверка на наличие секретных файлов...
set SECRETS_FOUND=0

if exist "service_account.json" (
    echo [⚠] Найден файл service_account.json
    set SECRETS_FOUND=1
)

findstr /C:"8481181310:AAGpndTUuT7NtJsJGpNAN3VsqZNYDzQs1PI" run_bot_simple.py >nul 2>nul
if %errorlevel% equ 0 (
    echo [⚠] В run_bot_simple.py обнаружен реальный токен бота
    set SECRETS_FOUND=1
)

if exist "feedback.xlsx" (
    echo [⚠] Найден файл feedback.xlsx с данными
    set SECRETS_FOUND=1
)

if exist "bot_log.txt" (
    echo [⚠] Найден файл bot_log.txt
    set SECRETS_FOUND=1
)

if !SECRETS_FOUND! equ 1 (
    echo.
    echo ВНИМАНИЕ: Обнаружены файлы с секретными данными!
    echo Эти файлы НЕ должны быть загружены на GitHub.
    echo Убедитесь, что они добавлены в .gitignore
    echo.
)

:: Проверка .gitignore
if not exist ".gitignore" (
    echo [✗] Файл .gitignore не найден!
    echo Создаём .gitignore...
    
    (
        echo # Secrets and credentials
        echo service_account.json
        echo *.json.bak
        echo config.ini
        echo secrets.py
        echo.
        echo # Local data files
        echo feedback.xlsx
        echo *.xlsx
        echo *.csv
        echo bot_log.txt
        echo *.log
        echo.
        echo # Python
        echo __pycache__/
        echo *.py[cod]
        echo *$py.class
        echo .venv/
        echo venv/
        echo ENV/
        echo.
        echo # IDE
        echo .vscode/
        echo .idea/
        echo *.swp
        echo.
        echo # OS
        echo .DS_Store
        echo Thumbs.db
    ) > .gitignore
    
    echo [✓] Файл .gitignore создан
) else (
    echo [✓] Файл .gitignore найден
)

:: Проверка README.md
if not exist "README.md" (
    echo [⚠] Файл README.md не найден
    echo Рекомендуется создать README.md с описанием проекта
) else (
    echo [✓] Файл README.md найден
)

:: Инициализация Git репозитория
echo.
echo Инициализация Git репозитория...

if not exist ".git" (
    git init
    echo [✓] Git репозиторий инициализирован
) else (
    echo [✓] Git репозиторий уже существует
)

:: Настройка Git (если нужно)
git config user.name >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Настройте Git:
    set /p username="Введите ваше имя: "
    set /p useremail="Введите ваш email: "
    git config user.name "!username!"
    git config user.email "!useremail!"
    echo [✓] Git настроен
)

:: Проверка файлов для коммита
echo.
echo Файлы для добавления в Git:
git status --short

echo.
set /p confirm="Добавить все файлы в Git? (y/n): "

if /i "!confirm!"=="y" (
    git add .
    echo [✓] Файлы добавлены
    
    echo.
    set /p commit_msg="Введите сообщение коммита (по умолчанию: 'Initial commit'): "
    if "!commit_msg!"=="" set commit_msg=Initial commit
    
    git commit -m "!commit_msg!"
    echo [✓] Коммит создан
)

:: Инструкции для GitHub
echo.
echo ==========================================
echo Следующие шаги для публикации на GitHub:
echo ==========================================
echo.
echo 1. Создайте новый репозиторий на GitHub:
echo    https://github.com/new
echo.
echo 2. Выполните следующие команды:
echo.
echo    git remote add origin https://github.com/ВАШЕ_ИМЯ/ИМЯ_РЕПОЗИТОРИЯ.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 3. Проверьте, что секретные файлы НЕ загружены!
echo.
echo ==========================================
echo ВАЖНО: Безопасность
echo ==========================================
echo.
echo Убедитесь, что следующие файлы НЕ загружены на GitHub:
echo   - service_account.json
echo   - feedback.xlsx
echo   - bot_log.txt
echo   - любые файлы с токенами и паролями
echo.
echo [✓] Готово! Проект подготовлен к публикации.
echo.

pause
