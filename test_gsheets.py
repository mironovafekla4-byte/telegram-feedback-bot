import gspread
import sys
import os

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')

if not GOOGLE_SHEET_ID:
    print("ERROR: GOOGLE_SHEET_ID environment variable not set")
    print("Set it with: export GOOGLE_SHEET_ID=your_sheet_id")
    sys.exit(1)

try:
    gc = gspread.service_account(filename='service_account.json')
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    print("Successfully connected to:", sh.title)
    print("Sheets:", [ws.title for ws in sh.worksheets()])
    
    # Try to append a test row
    worksheet = sh.worksheet('Лист1')
    print("Current worksheet:", worksheet.title)
    
    # Get all values to see structure
    all_values = worksheet.get_all_values()
    print(f"Current rows: {len(all_values)}")
    if len(all_values) > 0:
        print(f"Headers: {all_values[0]}")
        if len(all_values) > 1:
            print(f"First data row: {all_values[1]}")
    
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()