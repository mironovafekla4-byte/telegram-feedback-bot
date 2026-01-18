#!/bin/bash

# Скрипт подготовки проекта к публикации на GitHub
# Автоматически проверяет наличие секретных файлов и создаёт чистую копию проекта

echo "=========================================="
echo "Подготовка проекта к публикации на GitHub"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git не установлен${NC}"
    echo "Установите Git: https://git-scm.com/downloads"
    exit 1
fi

echo -e "${GREEN}✓ Git установлен${NC}"

# Проверка на наличие секретных файлов
echo ""
echo "Проверка на наличие секретных файлов..."

SECRETS_FOUND=0

if [ -f "service_account.json" ]; then
    echo -e "${YELLOW}⚠ Найден файл service_account.json${NC}"
    SECRETS_FOUND=1
fi

if grep -q "8481181310:AAGpndTUuT7NtJsJGpNAN3VsqZNYDzQs1PI" run_bot_simple.py 2>/dev/null; then
    echo -e "${YELLOW}⚠ В run_bot_simple.py обнаружен реальный токен бота${NC}"
    SECRETS_FOUND=1
fi

if [ -f "feedback.xlsx" ]; then
    echo -e "${YELLOW}⚠ Найден файл feedback.xlsx с данными${NC}"
    SECRETS_FOUND=1
fi

if [ -f "bot_log.txt" ]; then
    echo -e "${YELLOW}⚠ Найден файл bot_log.txt${NC}"
    SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}ВНИМАНИЕ: Обнаружены файлы с секретными данными!${NC}"
    echo "Эти файлы НЕ должны быть загружены на GitHub."
    echo "Убедитесь, что они добавлены в .gitignore"
    echo ""
fi

# Проверка .gitignore
if [ ! -f ".gitignore" ]; then
    echo -e "${RED}✗ Файл .gitignore не найден!${NC}"
    echo "Создаём .gitignore..."
    cat > .gitignore << 'EOF'
# Secrets and credentials
service_account.json
*.json.bak
config.ini
secrets.py

# Local data files
feedback.xlsx
*.xlsx
*.csv
bot_log.txt
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
EOF
    echo -e "${GREEN}✓ Файл .gitignore создан${NC}"
else
    echo -e "${GREEN}✓ Файл .gitignore найден${NC}"
fi

# Проверка README.md
if [ ! -f "README.md" ]; then
    echo -e "${YELLOW}⚠ Файл README.md не найден${NC}"
    echo "Рекомендуется создать README.md с описанием проекта"
else
    echo -e "${GREEN}✓ Файл README.md найден${NC}"
fi

# Инициализация Git репозитория
echo ""
echo "Инициализация Git репозитория..."

if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✓ Git репозиторий инициализирован${NC}"
else
    echo -e "${GREEN}✓ Git репозиторий уже существует${NC}"
fi

# Настройка Git (если нужно)
if [ -z "$(git config user.name)" ]; then
    echo ""
    echo "Настройте Git:"
    read -p "Введите ваше имя: " username
    read -p "Введите ваш email: " useremail
    git config user.name "$username"
    git config user.email "$useremail"
    echo -e "${GREEN}✓ Git настроен${NC}"
fi

# Проверка файлов для коммита
echo ""
echo "Файлы для добавления в Git:"
git status --short

echo ""
read -p "Добавить все файлы в Git? (y/n): " confirm

if [ "$confirm" == "y" ] || [ "$confirm" == "Y" ]; then
    git add .
    echo -e "${GREEN}✓ Файлы добавлены${NC}"
    
    echo ""
    read -p "Введите сообщение коммита (по умолчанию: 'Initial commit'): " commit_msg
    commit_msg=${commit_msg:-"Initial commit"}
    
    git commit -m "$commit_msg"
    echo -e "${GREEN}✓ Коммит создан${NC}"
fi

# Инструкции для GitHub
echo ""
echo "=========================================="
echo "Следующие шаги для публикации на GitHub:"
echo "=========================================="
echo ""
echo "1. Создайте новый репозиторий на GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Выполните следующие команды:"
echo ""
echo -e "${GREEN}   git remote add origin https://github.com/ВАШЕ_ИМЯ/ИМЯ_РЕПОЗИТОРИЯ.git${NC}"
echo -e "${GREEN}   git branch -M main${NC}"
echo -e "${GREEN}   git push -u origin main${NC}"
echo ""
echo "3. Проверьте, что секретные файлы НЕ загружены!"
echo ""
echo "=========================================="
echo "ВАЖНО: Безопасность"
echo "=========================================="
echo ""
echo "Убедитесь, что следующие файлы НЕ загружены на GitHub:"
echo "  - service_account.json"
echo "  - feedback.xlsx"
echo "  - bot_log.txt"
echo "  - любые файлы с токенами и паролями"
echo ""
echo "✓ Готово! Проект подготовлен к публикации."
