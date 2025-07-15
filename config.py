import os
from dotenv import load_dotenv

# Memuat semua variabel dari file .env ke dalam lingkungan
load_dotenv()

# --- Kunci API dan ID Dasar ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# --- Konfigurasi AI Modular ---
ACTIVE_AI_SERVICE = os.getenv("ACTIVE_AI_SERVICE", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# --- Nama Model AI Modular ---
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-vision")

# --- PETA FOLDER GOOGLE DRIVE (Moved from hardcoded) ---
FOLDER_MAP = {
    "BJ": os.getenv("FOLDER_BJ"),
    "BJM": os.getenv("FOLDER_BJM"),
    "SBY": os.getenv("FOLDER_SBY"),
    "SMD-BPN": os.getenv("FOLDER_SMD_BPN"),
    "SMG": os.getenv("FOLDER_SMG"),
}

# --- PETA NAMA SHEET (Moved from hardcoded) ---
SHEET_NAME_MAP = {
    "BJ": os.getenv("SHEET_BJ"),
    "SMG": os.getenv("SHEET_SMG"),
    "SBY": os.getenv("SHEET_SBY"),
    "BJM": os.getenv("SHEET_BJM"),
    "SMD-BPN": os.getenv("SHEET_SMD_BPN"),
}

# --- Validasi ---
if not all([TELEGRAM_BOT_TOKEN, GOOGLE_SHEET_ID]):
    raise ValueError("Kesalahan: Variabel TELEGRAM_BOT_TOKEN atau GOOGLE_SHEET_ID tidak ditemukan. Periksa file .env Anda.")

if ACTIVE_AI_SERVICE == 'openai' and not OPENAI_API_KEY:
    raise ValueError("Kesalahan: ACTIVE_AI_SERVICE diatur ke 'openai' tapi OPENAI_API_KEY tidak ditemukan.")
    
if ACTIVE_AI_SERVICE == 'deepseek' and not DEEPSEEK_API_KEY:
    raise ValueError("Kesalahan: ACTIVE_AI_SERVICE diatur ke 'deepseek' tapi DEEPSEEK_API_KEY tidak ditemukan.")

if not FOLDER_MAP or not SHEET_NAME_MAP:
    raise ValueError("Kesalahan: FOLDER_MAP atau SHEET_NAME_MAP di .env masih kosong. Mohon isi ID folder dan nama sheet.")

# Validasi semua folder dan sheet IDs ada
missing_folders = [branch for branch, folder_id in FOLDER_MAP.items() if not folder_id]
missing_sheets = [branch for branch, sheet_name in SHEET_NAME_MAP.items() if not sheet_name]

if missing_folders:
    raise ValueError(f"Kesalahan: ID folder tidak ditemukan untuk cabang: {missing_folders}. Periksa .env Anda.")

if missing_sheets:
    raise ValueError(f"Kesalahan: Nama sheet tidak ditemukan untuk cabang: {missing_sheets}. Periksa .env Anda.")