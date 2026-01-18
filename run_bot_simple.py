import telebot
from telebot import types
import pandas as pd
from datetime import datetime
import os
import sys
import re

# Импорты для Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Warning: gspread not installed. Install with: pip install gspread google-auth")

TOKEN = "8481181310:AAGpndTUuT7NtJsJGpNAN3VsqZNYDzQs1PI"
bot = telebot.TeleBot(TOKEN)

# ID Google Таблицы из ссылки
GOOGLE_SHEET_ID = "1fwB_P5s3hFddejrcmheG6C6dPE8TG7N3iQx5D6fPUzI"
SHEET_NAME = "Лист1"  # Название листа в Google Таблице

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
    
    # Путь к JSON файлу с ключами сервисного аккаунта
    # Файл должен называться service_account.json и лежать в папке бота
    service_account_file = r"C:\Users\GR203\Projects\feedback_bot\service_account.json"
    
    try:
        if os.path.exists(service_account_file):
            # Используем сервисный аккаунт для авторизации
            gc = gspread.service_account(filename=service_account_file)
            # Проверяем доступ к таблице
            sh = gc.open_by_key(GOOGLE_SHEET_ID)
            print(f"Successfully connected to Google Sheets: {sh.title}")
            return True
        else:
            print(f"Warning: Service account file '{service_account_file}' not found")
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
            print("7. Place it in the bot folder: Projects/feedback_bot/")
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
    
    # Преобразуем в строку, если это не строка
    if not isinstance(text, str):
        text = str(text)
    
    # Простой и надежный способ: удаляем все символы, которые нельзя закодировать в cp1251
    # Это автоматически удалит все эмодзи и специальные Unicode символы
    # Оставляем только символы, которые поддерживает Windows Excel (cp1251)
    try:
        # Удаляем все символы, которые не входят в cp1251
        # Сначала пробуем закодировать в cp1251, если ошибка - удаляем проблемные символы
        cleaned_chars = []
        for char in text:
            try:
                # Пробуем закодировать символ в cp1251
                char.encode('cp1251')
                cleaned_chars.append(char)
            except (UnicodeEncodeError, UnicodeDecodeError):
                # Если не получается закодировать - пропускаем этот символ (это эмодзи или спецсимвол)
                continue
        
        text_clean = ''.join(cleaned_chars)
        
        # Убираем множественные пробелы
        text_clean = ' '.join(text_clean.split())
        
        return text_clean.strip() if text_clean else ''
    except Exception:
        # В случае любой ошибки используем максимально простой метод
        try:
            # Удаляем все символы с кодом больше 255 (все эмодзи имеют код > 255)
            safe_chars = [char for char in text if ord(char) <= 255]
            text_clean = ''.join(safe_chars).strip()
            return text_clean if text_clean else ''
        except:
            # Последний резервный метод
            return str(text).encode('cp1251', 'ignore').decode('cp1251', 'ignore').strip() if text else ''

# Словарь для замены категорий с эмодзи на текстовые версии (если нужно)
# Новые категории без эмодзи
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
    """Загружает данные из Google Sheets, оставляя ТОЛЬКО 3 столбца: category, question, time"""
    global feedback_data
    feedback_data = []
    
    if gc:
        try:
            # Открываем таблицу по ID
            sh = gc.open_by_key(GOOGLE_SHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            
            # Получаем все данные
            all_values = worksheet.get_all_records()
            
            if all_values:
                # Очищаем загруженные данные от эмодзи и персональных данных
                # Создаём ТОЛЬКО 3 столбца: category, question, time
                cleaned_records = []
                for record in all_values:
                    # Извлекаем ТОЛЬКО нужные поля
                    cleaned_record = {
                        'category': clean_emoji_for_excel(str(record.get('category', record.get('Категория', '')))),
                        'question': clean_emoji_for_excel(str(record.get('question', record.get('Вопрос', '')))),
                        'time': str(record.get('time', record.get('Время', '')))
                    }
                    # Пропускаем записи, если все поля пустые
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
                existing_columns = df.columns.tolist()
                columns_to_keep = [col for col in required_columns if col in existing_columns]
                
                if columns_to_keep:
                    df = df[columns_to_keep].copy()
                    for col in required_columns:
                        if col not in df.columns:
                            df[col] = ''
                    
                    cleaned_records = []
                    for record in df.to_dict('records'):
                        cleaned_record = {
                            'category': clean_emoji_for_excel(str(record.get('category', ''))),
                            'question': clean_emoji_for_excel(str(record.get('question', ''))),
                            'time': str(record.get('time', ''))
                        }
                        cleaned_records.append(cleaned_record)
                    
                    feedback_data = cleaned_records
                    print(f"Loaded {len(feedback_data)} records from Excel (fallback)")
        except Exception as e:
            print(f"Error loading data: {e}")
            feedback_data = []

# Инициализируем Google Sheets перед загрузкой данных
sheets_available = init_google_sheets()
if sheets_available:
    print("Google Sheets connection initialized successfully")
else:
    print("Warning: Google Sheets not available, will use local Excel as fallback")

load_existing_data()

@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        user_questions[message.chat.id] = None
        print(f"[/start] User: {message.from_user.id} (@{message.from_user.username})")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Операционные вопросы', 'КС', 'СУЗ')
        markup.add('СЭО', 'Логистика', 'HR')
        markup.add('Другое')
        bot.send_message(message.chat.id, 
                        "🔍 Задай вопрос руководителю\nВыбери категорию:", 
                        reply_markup=markup)
        print(f"[/start] Message sent to chat {message.chat.id}")
    except Exception as e:
        print(f"ERROR in start_message: {e}")
        import traceback
        traceback.print_exc()

@bot.message_handler(func=lambda message: message.text == '🔄 Новый вопрос')
def new_question(message):
    user_questions[message.chat.id] = None
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Операционные вопросы', 'КС', 'СУЗ')
        markup.add('СЭО', 'Логистика', 'HR')
        markup.add('Другое')
        bot.send_message(message.chat.id, 
                        "🔄 Выбери категорию для нового вопроса:", 
                        reply_markup=markup)
    except Exception as e:
        print(f"Error in new_question: {e}")

@bot.message_handler(func=lambda message: message.text in ['Операционные вопросы', 'КС', 'СУЗ', 'СЭО', 'Логистика', 'HR', 'Другое'])
def ask_question(message):
    category = message.text
    user_questions[message.chat.id] = {'category': category, 'text': ''}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('✅ Отправить', '🔄 Новый вопрос')
    msg = bot.send_message(message.chat.id, 
                          f"{category}\n💬 Опиши вопрос:", 
                          reply_markup=markup)
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
            # Сообщение об успешном сохранении отправляется внутри save_feedback
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
    """Сохраняет обратную связь в Google Sheets с ТОЛЬКО 3 столбцами: category, question, time (без персональных данных)"""
    global feedback_data
    try:
        # Очищаем эмодзи из категории и текста
        category_clean = category_map.get(category, clean_emoji_for_excel(category))
        text_clean = clean_emoji_for_excel(text) if text else text
        
        # Создаём новую запись
        feedback_entry = {
            'category': category_clean,
            'question': text_clean,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        feedback_data.append(feedback_entry)
        
        # Сохраняем в Google Sheets
        if gc:
            try:
                # Открываем таблицу
                sh = gc.open_by_key(GOOGLE_SHEET_ID)
                worksheet = sh.worksheet(SHEET_NAME)
                
                # Получаем текущие данные
                all_values = worksheet.get_all_values()
                
                # Проверяем наличие правильных заголовков
                expected_headers = ['Категория', 'Вопрос', 'Время']
                has_correct_headers = False
                
                if all_values and len(all_values) > 0:
                    # Проверяем, есть ли правильные заголовки в первой строке
                    first_row = all_values[0]
                    # Проверяем точное совпадение или частичное (case-insensitive)
                    if (first_row == expected_headers or 
                        (len(first_row) >= 3 and 
                         (first_row[0].lower().strip() in ['категория', 'category'] or 'категория' in first_row[0].lower()) and
                         (first_row[1].lower().strip() in ['вопрос', 'question'] or 'вопрос' in first_row[1].lower()) and
                         (first_row[2].lower().strip() in ['время', 'time'] or 'время' in first_row[2].lower()))):
                        has_correct_headers = True
                        print("Headers found in Google Sheets")
                
                # Если заголовков нет, создаём их
                if not has_correct_headers:
                    if all_values and len(all_values) > 0:
                        # Вставляем заголовки в начало (index 1 означает вставку перед существующими данными)
                        try:
                            worksheet.insert_row(expected_headers, index=1)
                            print("Created headers in Google Sheets (inserted at top)")
                        except Exception as insert_error:
                            # Если insert не работает, добавляем в начало другим способом
                            print(f"Warning: Could not insert headers ({insert_error}), trying alternative method")
                            # Обновляем первую строку заголовками
                            worksheet.update('A1:C1', [expected_headers])
                            print("Updated first row with headers")
                    else:
                        # Таблица пустая, просто добавляем заголовки
                        worksheet.append_row(expected_headers)
                        print("Created headers in empty Google Sheets")
                
                # Добавляем новую строку (без эмодзи и персональных данных)
                new_row = [category_clean, text_clean, feedback_entry['time']]
                worksheet.append_row(new_row)
                
                print(f"Saved to Google Sheets: {category_clean} | {text_clean[:50] if text_clean else 'empty'}...")
                
                # Обновляем сообщение для пользователя
                bot.send_message(message.chat.id, "✅ Вопрос сохранён", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add('🔄 Новый вопрос'))
                return
                
            except Exception as gs_error:
                print(f"Error saving to Google Sheets: {gs_error}")
                # Fallback на локальное сохранение
                pass
        
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
        bot.send_message(message.chat.id, "✅ Вопрос сохранён", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add('🔄 Новый вопрос'))
        
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

print("="*50)
print("Bot starting...")
print("="*50)
try:
    print("Bot info:", bot.get_me())
    print("Starting polling...")
    bot.polling(none_stop=True, interval=0, timeout=20)
except KeyboardInterrupt:
    print("\nBot stopped by user")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
