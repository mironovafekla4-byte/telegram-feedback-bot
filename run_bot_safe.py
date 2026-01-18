import telebot
from telebot import types
import pandas as pd
from datetime import datetime
import os
import sys

# Импорты для Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Warning: gspread not installed. Install with: pip install gspread google-auth")

# ============================================================
# КОНФИГУРАЦИЯ - ОБЯЗАТЕЛЬНО ЗАПОЛНИТЕ ПЕРЕД ЗАПУСКОМ!
# ============================================================

# Способ 1: Переменные окружения (РЕКОМЕНДУЕТСЯ)
# Установите переменные окружения перед запуском:
# export BOT_TOKEN="ваш_токен"
# export GOOGLE_SHEET_ID="id_таблицы"

TOKEN = os.getenv('BOT_TOKEN') or "УКАЖИТЕ_ВАШ_ТОКЕН_ЗДЕСЬ"
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID') or "УКАЖИТЕ_ID_ТАБЛИЦЫ_ЗДЕСЬ"

# Способ 2: Импорт из config.py (если создан)
# try:
#     from config import BOT_TOKEN, GOOGLE_SHEET_ID
#     TOKEN = BOT_TOKEN
# except ImportError:
#     pass

# ============================================================

SHEET_NAME = "Лист1"  # Название листа в Google Таблице
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE') or "service_account.json"

# Проверка конфигурации
if TOKEN == "УКАЖИТЕ_ВАШ_ТОКЕН_ЗДЕСЬ" or not TOKEN:
    print("="*60)
    print("ОШИБКА: Токен бота не настроен!")
    print("="*60)
    print("Установите переменную окружения BOT_TOKEN:")
    print("  Windows: set BOT_TOKEN=ваш_токен")
    print("  Linux/Mac: export BOT_TOKEN=ваш_токен")
    print("")
    print("Или укажите токен напрямую в коде (НЕ рекомендуется для Git)")
    print("="*60)
    sys.exit(1)

if GOOGLE_SHEET_ID == "УКАЖИТЕ_ID_ТАБЛИЦЫ_ЗДЕСЬ" or not GOOGLE_SHEET_ID:
    print("="*60)
    print("ПРЕДУПРЕЖДЕНИЕ: ID Google Таблицы не настроен!")
    print("="*60)
    print("Бот будет работать только с локальным Excel файлом.")
    print("Для работы с Google Sheets установите переменную окружения:")
    print("  GOOGLE_SHEET_ID=id_вашей_таблицы")
    print("="*60)

bot = telebot.TeleBot(TOKEN)

feedback_data = []
user_questions = {}

# Переменная для клиента Google Sheets
gc = None

def init_google_sheets():
    """Инициализация подключения к Google Sheets через сервисный аккаунт"""
    global gc
    if not GOOGLE_SHEETS_AVAILABLE:
        print("Warning: gspread library not installed")
        return False

    if GOOGLE_SHEET_ID == "УКАЖИТЕ_ID_ТАБЛИЦЫ_ЗДЕСЬ" or not GOOGLE_SHEET_ID:
        print("Google Sheets ID not configured, using local Excel only")
        return False

    try:
        # Способ 1: Credentials из переменной окружения (для Render, Heroku и др.)
        google_creds = os.getenv('GOOGLE_CREDENTIALS')
        if google_creds:
            import json
            creds_dict = json.loads(google_creds)
            gc = gspread.service_account_from_dict(creds_dict)
            sh = gc.open_by_key(GOOGLE_SHEET_ID)
            print(f"Successfully connected to Google Sheets (from env): {sh.title}")
            return True
        # Способ 2: Credentials из файла (для локальной разработки)
        elif os.path.exists(SERVICE_ACCOUNT_FILE):
            gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
            sh = gc.open_by_key(GOOGLE_SHEET_ID)
            print(f"Successfully connected to Google Sheets: {sh.title}")
            return True
        else:
            print(f"Warning: Service account file '{SERVICE_ACCOUNT_FILE}' not found")
            print("="*60)
            print("INSTRUCTIONS TO SET UP GOOGLE SHEETS:")
            print("="*60)
            print("1. Go to: https://console.cloud.google.com/")
            print("2. Create a new project or select existing one")
            print("3. Enable Google Sheets API:")
            print("   - APIs & Services > Library > Search 'Google Sheets API' > Enable")
            print("4. Create Service Account:")
            print("   - APIs & Services > Credentials > Create Credentials > Service Account")
            print("   - Give it a name and create")
            print("5. Create Key:")
            print("   - Click on created service account > Keys > Add Key > JSON")
            print("   - Download the JSON file")
            print("6. Rename JSON file to 'service_account.json'")
            print("7. Place it in the bot folder")
            print("8. Share your Google Sheet with the service account email")
            print("   (Email is in the JSON file, field 'client_email')")
            print("="*60)
            return False
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        print("Make sure:")
        print("1. service_account.json file exists and is valid")
        print("2. Google Sheet is shared with the service account email")
        print("3. Google Sheets API is enabled in your project")
        return False

# Функция для очистки эмодзи из текста при сохранении в Excel
def clean_emoji_for_excel(text):
    """Удаляет ВСЕ эмодзи и специальные символы из текста для корректного сохранения в Excel"""
    if not text:
        return ''
    
    if not isinstance(text, str):
        text = str(text)
    
    try:
        cleaned_chars = []
        for char in text:
            try:
                char.encode('cp1251')
                cleaned_chars.append(char)
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        
        text_clean = ''.join(cleaned_chars)
        text_clean = ' '.join(text_clean.split())
        
        return text_clean.strip() if text_clean else ''
    except Exception:
        try:
            safe_chars = [char for char in text if ord(char) <= 255]
            text_clean = ''.join(safe_chars).strip()
            return text_clean if text_clean else ''
        except:
            return str(text).encode('cp1251', 'ignore').decode('cp1251', 'ignore').strip() if text else ''

# Словарь для замены категорий с эмодзи на текстовые версии
category_map = {
    'Операционные вопросы': 'Операционные вопросы',
    'КС': 'КС',
    'СУЗ': 'СУЗ',
    'СЭО': 'СЭО',
    'Логистика': 'Логистика',
    'HR': 'HR',
    'Другое': 'Другое'
}

def load_existing_data():
    """Загружает данные из Google Sheets или локального Excel файла"""
    global feedback_data
    feedback_data = []
    
    if gc:
        try:
            sh = gc.open_by_key(GOOGLE_SHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_values = worksheet.get_all_records()
            
            if all_values:
                cleaned_records = []
                for record in all_values:
                    cleaned_record = {
                        'category': clean_emoji_for_excel(str(record.get('category', record.get('Категория', '')))),
                        'question': clean_emoji_for_excel(str(record.get('question', record.get('Вопрос', '')))),
                        'time': str(record.get('time', record.get('Время', '')))
                    }
                    if cleaned_record['category'] or cleaned_record['question']:
                        cleaned_records.append(cleaned_record)
                
                feedback_data = cleaned_records
                print(f"Loaded {len(feedback_data)} records from Google Sheets")
        except Exception as e:
            print(f"Error loading data from Google Sheets: {e}")
            feedback_data = []
    else:
        # Fallback на локальный Excel файл
        try:
            if os.path.exists('feedback.xlsx'):
                df = pd.read_excel('feedback.xlsx', engine='openpyxl')
                required_columns = ['category', 'question', 'time']
                
                if all(col in df.columns for col in required_columns):
                    feedback_data = df[required_columns].to_dict('records')
                    print(f"Loaded {len(feedback_data)} records from local Excel")
        except Exception as e:
            print(f"Error loading local Excel: {e}")
            feedback_data = []

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📦 Операционные вопросы', '💼 КС')
    markup.add('🔧 СУЗ', '⚡ СЭО')
    markup.add('🚚 Логистика', '👥 HR')
    markup.add('📝 Другое')
    bot.send_message(message.chat.id, "👋 Привет! Выбери категорию вопроса:", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🤖 Помощь по использованию бота:

1️⃣ Нажми /start чтобы начать
2️⃣ Выбери категорию вопроса
3️⃣ Опиши свой вопрос
4️⃣ Нажми '✅ Отправить'

Команды:
/start - Начать работу
/stats - Статистика по категориям
/help - Эта справка

Все вопросы сохраняются анонимно! 🔒
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: message.text == '🔄 Новый вопрос')
def new_question(message):
    start(message)

@bot.message_handler(func=lambda message: message.text in [
    '📦 Операционные вопросы', '💼 КС', '🔧 СУЗ', 
    '⚡ СЭО', '🚚 Логистика', '👥 HR', '📝 Другое'
])
def category_selected(message):
    category = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('✅ Отправить', '🔄 Новый вопрос')
    msg = bot.send_message(message.chat.id, f"{category}\n💬 Опиши вопрос:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_feedback, category)

def process_feedback(message, category):
    if message.text and message.text.startswith('/'):
        bot.process_new_messages([message])
        return
    
    if message.text == '✅ Отправить':
        if message.chat.id in user_questions and user_questions[message.chat.id] and user_questions[message.chat.id].get('text'):
            save_feedback(message, category, user_questions[message.chat.id]['text'])
            user_questions[message.chat.id] = None
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('🔄 Новый вопрос')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('✅ Отправить', '🔄 Новый вопрос')
            bot.send_message(message.chat.id, "⚠️ Сначала опиши вопрос, затем нажми 'Отправить'", reply_markup=markup)
            msg = bot.send_message(message.chat.id, f"{category}\n💬 Опиши вопрос:")
            bot.register_next_step_handler(msg, process_feedback, category)
    elif message.text == '🔄 Новый вопрос':
        new_question(message)
    else:
        if message.chat.id not in user_questions:
            user_questions[message.chat.id] = {}
        user_questions[message.chat.id] = {'category': category, 'text': message.text}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('✅ Отправить', '🔄 Новый вопрос')
        msg = bot.send_message(message.chat.id, "✅ Вопрос сохранён. Нажми 'Отправить' для отправки или продолжи ввод.", reply_markup=markup)
        bot.register_next_step_handler(msg, process_feedback, category)

def save_feedback(message, category, text):
    """Сохраняет обратную связь в Google Sheets или локальный Excel"""
    global feedback_data
    try:
        category_clean = category_map.get(category, clean_emoji_for_excel(category))
        text_clean = clean_emoji_for_excel(text) if text else text
        
        feedback_entry = {
            'category': category_clean,
            'question': text_clean,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        feedback_data.append(feedback_entry)
        
        # Сохраняем в Google Sheets
        if gc:
            try:
                sh = gc.open_by_key(GOOGLE_SHEET_ID)
                worksheet = sh.worksheet(SHEET_NAME)
                
                all_values = worksheet.get_all_values()
                expected_headers = ['Категория', 'Вопрос', 'Время']
                
                if not all_values or all_values[0] != expected_headers:
                    if all_values:
                        worksheet.insert_row(expected_headers, index=1)
                    else:
                        worksheet.append_row(expected_headers)
                
                new_row = [category_clean, text_clean, feedback_entry['time']]
                worksheet.append_row(new_row)
                
                print(f"Saved to Google Sheets: {category_clean} | {text_clean[:50] if text_clean else 'empty'}...")
                
                bot.send_message(message.chat.id, "✅ Вопрос сохранён", 
                               reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add('🔄 Новый вопрос'))
                return
                
            except Exception as gs_error:
                print(f"Error saving to Google Sheets: {gs_error}")
        
        # Fallback: сохраняем в локальный Excel
        cleaned_data = []
        for entry in feedback_data:
            cleaned_entry = {
                'category': clean_emoji_for_excel(str(entry.get('category', ''))),
                'question': clean_emoji_for_excel(str(entry.get('question', ''))),
                'time': str(entry.get('time', ''))
            }
            cleaned_data.append(cleaned_entry)
        
        df = pd.DataFrame(cleaned_data, columns=['category', 'question', 'time'])
        
        try:
            with pd.ExcelWriter('feedback.xlsx', engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Feedback')
        except Exception as excel_error:
            print(f"Warning with openpyxl: {excel_error}, trying alternative method")
            df.to_excel('feedback.xlsx', index=False, engine='openpyxl')
        
        print(f"Saved to Excel (fallback): {category_clean} | {text_clean[:50] if text_clean else 'empty'}...")
        bot.send_message(message.chat.id, "✅ Вопрос сохранён", 
                       reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add('🔄 Новый вопрос'))
        
    except Exception as e:
        print(f"Error saving: {e}")
        import traceback
        traceback.print_exc()
        try:
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii') if str(e) else "Unknown error"
        except:
            error_msg = "Error saving"
        bot.send_message(message.chat.id, f"Ошибка при сохранении: {error_msg}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if not feedback_data:
        bot.send_message(message.chat.id, "📊 Пока нет отзывов")
        return
    try:
        df = pd.DataFrame(feedback_data)
        stats = df['category'].value_counts().to_dict()
        total = len(feedback_data)
        text = f"📊 СТАТИСТИКА ({total} отзывов):\n\n"
        for cat, count in stats.items():
            text += f"{cat}: {count}\n"
        bot.send_message(message.chat.id, text)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при получении статистики: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.chat.id in user_questions and user_questions[message.chat.id]:
        category = user_questions[message.chat.id]['category']
        process_feedback(message, category)
    else:
        bot.send_message(message.chat.id, "👋 Для начала работы отправь /start")

# Инициализация и запуск
print("="*50)
print("Bot starting...")
print("="*50)

# Инициализируем Google Sheets
if init_google_sheets():
    print("✓ Google Sheets connection established")
    load_existing_data()
else:
    print("! Using local Excel file for storage")

try:
    print("Bot info:", bot.get_me())
    print("Starting polling...")
    print("="*50)
    bot.polling(none_stop=True, interval=0, timeout=20)
except KeyboardInterrupt:
    print("\nBot stopped by user")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
