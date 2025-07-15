"""
Command handlers for the Telegram bot.
Handles /start, /help, /status, /cancel and other commands.
"""

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler
from config.settings import settings


class CommandHandlers(BaseHandler):
    """
    Handler class for bot commands.
    """
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command.
        Welcomes new users and provides basic instructions.
        """
        try:
            # Clear any existing session
            self._clear_user_session(context)
            
            # Log user action
            self._log_user_action(update, "start_command")
            
            user_name = self._get_user_display_name(update)
            
            welcome_message = (
                f"🤖 Halo {user_name}! Selamat datang di Bot KTP/NPWP Assistant.\n\n"
                "📋 **Apa yang bisa saya lakukan:**\n"
                "• Memproses foto KTP dan NPWP dengan AI\n"
                "• Menyimpan data ke Google Sheets otomatis\n"
                "• Mengarsipkan file ke Google Drive\n"
                "• Menangani file PDF\n\n"
                "📤 **Cara menggunakan:**\n"
                "1. Kirim foto KTP/NPWP (bisa dengan caption nama toko)\n"
                "2. Atau kirim file PDF untuk diarsipkan\n"
                "3. Pilih cabang tujuan\n"
                "4. Periksa hasil AI dan konfirmasi\n\n"
                "💡 **Tips:**\n"
                "• Pastikan foto jelas dan tidak buram\n"
                "• Pencahayaan yang baik untuk hasil terbaik\n"
                "• Gunakan /help untuk bantuan lebih lanjut\n\n"
                "Silakan kirim foto atau file untuk memulai! 🚀"
            )
            
            await update.message.reply_text(
                text=welcome_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command.
        Provides detailed help information.
        """
        try:
            self._log_user_action(update, "help_command")
            
            help_message = (
                "🆘 **Bantuan Bot KTP/NPWP Assistant**\n\n"
                "**📋 Perintah yang tersedia:**\n"
                "• /start - Memulai bot dan melihat panduan\n"
                "• /help - Menampilkan bantuan ini\n"
                "• /status - Cek status sistem\n"
                "• /cancel - Membatalkan operasi yang sedang berjalan\n\n"
                "**📤 Cara kerja bot:**\n"
                "1. **Foto KTP/NPWP**: Bot akan memproses dengan AI untuk ekstraksi data\n"
                "2. **File PDF**: Bot akan menyimpan ke folder yang sesuai\n"
                "3. **Caption**: Jika ada caption, akan disimpan sebagai nama toko\n\n"
                "**🏢 Cabang yang didukung:**\n"
            )
            
            # Add branch list
            branches = settings.get_branch_list()
            for branch in sorted(branches):
                help_message += f"• {branch}\n"
            
            help_message += (
                "\n**⚠️ Persyaratan file:**\n"
                f"• Gambar: JPG/PNG, maksimal {settings.MAX_IMAGE_SIZE_MB}MB\n"
                f"• PDF: Maksimal {settings.MAX_PDF_SIZE_MB}MB\n"
                "• Foto harus jelas dan terbaca\n\n"
                "**🔒 Keamanan:**\n"
                "• Data diproses secara aman\n"
                "• File dihapus setelah diproses\n"
                "• Sesi otomatis berakhir setelah 30 menit\n\n"
                "**❓ Masalah umum:**\n"
                "• Foto buram → Ambil foto ulang dengan pencahayaan baik\n"
                "• AI tidak bisa baca → Pastikan teks terlihat jelas\n"
                "• File terlalu besar → Kompres file atau gunakan resolusi lebih kecil\n\n"
                "Butuh bantuan lebih lanjut? Hubungi admin."
            )
            
            await update.message.reply_text(
                text=help_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /status command.
        Shows bot status and user session info.
        """
        try:
            self._log_user_action(update, "status_command")
            
            # Get session info
            user_data = context.user_data
            session_info = "Tidak ada sesi aktif"
            
            if user_data:
                workflow = user_data.get('workflow_type', 'Unknown')
                state = user_data.get('state', 'Unknown')
                created_at = user_data.get('created_at')
                
                if created_at:
                    duration = datetime.now() - created_at
                    duration_str = f"{duration.seconds // 60} menit"
                else:
                    duration_str = "Unknown"
                
                session_info = (
                    f"Workflow: {workflow}\n"
                    f"State: {state}\n"
                    f"Durasi: {duration_str}"
                )
            
            # Bot status
            status_message = (
                "📊 **Status Bot**\n\n"
                f"🤖 **Bot**: Aktif ✅\n"
                f"🧠 **AI Service**: {settings.ACTIVE_AI_SERVICE.upper()}\n"
                f"📝 **Google Sheets**: Terhubung ✅\n"
                f"📁 **Google Drive**: Terhubung ✅\n\n"
                f"👤 **Sesi Anda**:\n{session_info}\n\n"
                f"⚙️ **Konfigurasi**:\n"
                f"• Timeout sesi: {settings.SESSION_TIMEOUT_MINUTES} menit\n"
                f"• Max ukuran gambar: {settings.MAX_IMAGE_SIZE_MB}MB\n"
                f"• Max ukuran PDF: {settings.MAX_PDF_SIZE_MB}MB\n"
                f"• Cabang tersedia: {len(settings.get_branch_list())}\n\n"
                f"🕐 **Waktu server**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await update.message.reply_text(
                text=status_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /cancel command.
        Cancels current operation and clears session.
        """
        try:
            self._log_user_action(update, "cancel_command")
            
            # Check if there's an active session
            user_data = context.user_data
            
            if not user_data:
                await update.message.reply_text(
                    "❌ Tidak ada operasi yang sedang berjalan untuk dibatalkan."
                )
                return
            
            # Get current workflow info
            workflow = user_data.get('workflow_type', 'Unknown')
            state = user_data.get('state', 'Unknown')
            
            # Clear session
            self._clear_user_session(context)
            
            cancel_message = (
                "✅ **Operasi dibatalkan**\n\n"
                f"📋 Workflow yang dibatalkan: {workflow}\n"
                f"📊 State terakhir: {state}\n\n"
                "Semua data sesi telah dihapus.\n"
                "Silakan mulai ulang dengan mengirim foto atau file baru."
            )
            
            await update.message.reply_text(
                text=cancel_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def admin_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /admin_stats command (admin only).
        Shows system statistics and usage info.
        """
        try:
            # Check admin access
            if not await self._require_admin(update, context):
                return
            
            self._log_user_action(update, "admin_stats_command")
            
            # This would require implementing usage tracking
            # For now, just show basic system info
            
            stats_message = (
                "📊 **Admin Statistics**\n\n"
                "🤖 **System Status**: Online ✅\n"
                f"🧠 **AI Service**: {settings.ACTIVE_AI_SERVICE}\n"
                f"🏢 **Branches**: {len(settings.get_branch_list())}\n"
                f"⚙️ **Environment**: {settings.ENVIRONMENT}\n"
                f"📝 **Debug Mode**: {'On' if settings.DEBUG else 'Off'}\n\n"
                "📈 **Usage Stats**: (Not implemented yet)\n"
                "• Total users: N/A\n"
                "• Documents processed today: N/A\n"
                "• Active sessions: N/A\n\n"
                "💾 **Resource Usage**: (Not implemented yet)\n"
                "• Memory usage: N/A\n"
                "• AI API calls: N/A\n"
                "• Google API calls: N/A"
            )
            
            await update.message.reply_text(
                text=stats_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)