# 🤖 Telegram KTP/NPWP Bot

AI-powered document processing bot untuk dokumen KTP dan NPWP Indonesia. Bot ini menggunakan AI untuk ekstraksi data otomatis, kemudian menyimpan ke Google Sheets dan mengarsipkan file ke Google Drive.

## ✨ Features

- 📸 **AI Document Processing** - Ekstraksi data KTP/NPWP otomatis menggunakan OpenAI/DeepSeek
- 📊 **Google Sheets Integration** - Simpan data langsung ke spreadsheet
- 📁 **Google Drive Storage** - Arsipkan dokumen dengan organisasi folder otomatis
- ✏️ **Data Editing** - Edit data hasil AI sebelum disimpan
- 🏢 **Multi-Branch Support** - Mendukung multiple cabang/lokasi
- 📄 **PDF Handling** - Upload dan organisir file PDF

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/iunoo/bot-autoinput-npwpktp.git
cd bot-autoinput-npwpktp
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
# Copy template dan isi dengan data Anda
cp .env.example .env
# Edit .env dengan text editor
```

### 3. Setup Google Credentials
```bash
# Buat folder credentials
mkdir credentials

# Download dari Google Cloud Console dan simpan sebagai:
# credentials/credentials.json
```

### 4. Run Bot
```bash
python main.py
```

## ⚙️ Configuration

### Required API Keys
- **Telegram Bot Token** - Dari @BotFather
- **OpenAI API Key** - Dari platform.openai.com (atau)
- **DeepSeek API Key** - Dari platform.deepseek.com  
- **Google Credentials** - Dari Google Cloud Console

### Environment Variables
Lihat `.env.example` untuk template lengkap.

### Google Drive Folder Structure
```
Branch Folder/
├── Sudah diinput/     # Processed documents
└── PDF/              # PDF files
```

## 🎯 Usage

1. **Kirim foto KTP/NPWP** ke bot
2. **Pilih cabang** tujuan penyimpanan
3. **Review data** hasil AI extraction
4. **Edit jika perlu** dengan tombol Edit
5. **Konfirmasi & simpan** ke Sheets + Drive

### Supported Commands
- `/start` - Mulai bot
- `/help` - Bantuan lengkap
- `/status` - Cek status bot & session
- `/cancel` - Batalkan operasi

## 🛠️ Maintenance

### Regular Tasks
- **Monthly**: Cek log errors (optional)
- **Quarterly**: Backup credential files
- **As needed**: Update dependencies

### Troubleshooting
- **Bot tidak respon**: Restart dengan `python main.py`
- **AI error**: Coba foto yang lebih jelas
- **Google error**: Cek internet & credentials
- **Token expired**: Bot akan auto-refresh

## 📁 Project Structure

```
├── config/           # Configuration management
├── core/            # Core business logic & bot
├── handlers/        # Telegram message handlers  
├── models/          # Data models & session management
├── services/        # External service integrations
├── utils/           # Utility functions & keyboards
├── credentials/     # Google API credentials (gitignored)
├── logs/           # Application logs (gitignored)
├── .env            # Environment variables (gitignored)
└── main.py         # Application entry point
```

## 🔒 Security Notes

- Semua credentials di-gitignore
- Token auto-refresh untuk Google API
- Data sensitif hanya di environment variables
- File credentials tidak pernah di-commit

## 📊 Stats & Monitoring

Check bot status dengan `/status` command:
- Active AI service & model
- Google services connection
- Session information
- System configuration

## 🚨 Common Issues

### "AI tidak bisa baca gambar"
- Pastikan foto jelas dan tidak blur
- Cek pencahayaan cukup
- Pastikan teks terbaca dengan baik

### "Google service error"  
- Cek koneksi internet
- Verify credentials masih valid
- Cek quota Google API (jarang terjadi)

### "Session expired"
- Normal setelah 30 menit tidak aktif
- Restart dengan `/start`

## 🛡️ Backup Strategy

### Critical Files to Backup:
```bash
credentials/credentials.json
credentials/token.json  
.env
```

### Optional:
```bash
logs/                # For debugging
```

## 📈 Future Enhancements

- [ ] Batch document processing
- [ ] OCR confidence scoring  
- [ ] Document templates
- [ ] Usage analytics
- [ ] Mobile app integration

---

**Last Updated**: July 2025  
**Version**: 1.0.0
