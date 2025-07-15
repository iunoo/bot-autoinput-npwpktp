"""
Message handlers for the Telegram bot.
Handles photo, PDF, and text messages with improved structure.
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler
from config.settings import settings
from config.constants import (
    SUPPORTED_IMAGE_TYPES, 
    SUPPORTED_DOCUMENT_TYPES,
    ERROR_MESSAGES
)
from core.exceptions import InvalidFileError, ValidationError
from utils.keyboards import get_branch_keyboard


class MessageHandlers(BaseHandler):
    """
    Handler class for different types of messages.
    """
    
    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle photo messages (KTP/NPWP images).
        """
        try:
            # Send typing indicator
            await self._send_typing_action(update, context)
            
            # Log user action
            self._log_user_action(update, "photo_upload", {
                "has_caption": bool(update.message.caption)
            })
            
            # Validate file
            photo_file = update.message.photo[-1]  # Get highest resolution
            await self._validate_photo_file(photo_file)
            
            # Initialize photo workflow session
            self._init_user_session(context, 'photo')
            
            # Store file info
            self._set_session_data(context, 'file_id', photo_file.file_id)
            self._set_session_data(context, 'file_size', photo_file.file_size)
            
            # Handle caption if present
            caption_message = ""
            if update.message.caption:
                caption = update.message.caption.strip()
                self._set_session_data(context, 'nama_toko', caption)
                caption_message = f"Caption '{caption}' disimpan sebagai nama toko.\n\n"
            
            # Set state to awaiting branch selection
            self._set_session_state(context, 'awaiting_branch')
            
            response_message = (
                "📸 **Foto diterima!**\n\n"
                f"{caption_message}"
                "Silakan pilih cabang tujuan untuk menyimpan data:"
            )
            
            await update.message.reply_text(
                text=response_message,
                reply_markup=get_branch_keyboard(),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_pdf_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle PDF document messages.
        """
        try:
            # Send typing indicator
            await self._send_typing_action(update, context)
            
            # Log user action
            self._log_user_action(update, "pdf_upload", {
                "filename": update.message.document.file_name,
                "file_size": update.message.document.file_size
            })
            
            # Validate file
            document = update.message.document
            await self._validate_pdf_file(document)
            
            # Initialize PDF workflow session
            self._init_user_session(context, 'pdf')
            
            # Store file info
            self._set_session_data(context, 'file_id', document.file_id)
            self._set_session_data(context, 'file_size', document.file_size)
            self._set_session_data(context, 'original_filename', document.file_name)
            
            # Set state to awaiting branch selection
            self._set_session_state(context, 'awaiting_branch')
            
            file_size = self._format_file_size(document.file_size)
            
            response_message = (
                "📄 **PDF diterima!**\n\n"
                f"📋 **File**: {document.file_name}\n"
                f"📊 **Ukuran**: {file_size}\n\n"
                "Silakan pilih cabang tujuan untuk menyimpan file:"
            )
            
            await update.message.reply_text(
                text=response_message,
                reply_markup=get_branch_keyboard(),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle text messages based on current session state.
        """
        try:
            # Get current session state
            current_state = self._get_session_state(context)
            
            if not current_state:
                # No active session, provide guidance
                await self._handle_no_active_session(update, context)
                return
            
            # Handle based on state
            if current_state == 'awaiting_pdf_name':
                await self._handle_pdf_naming(update, context)
            elif current_state == 'awaiting_edit_input':
                await self._handle_data_edit(update, context)
            else:
                # Unexpected text message
                await self._handle_unexpected_text(update, context)
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def _validate_photo_file(self, photo_file) -> None:
        """Validate photo file size and type."""
        # Check file size
        if photo_file.file_size:
            if not self._validate_file_size(photo_file.file_size, settings.MAX_IMAGE_SIZE_MB):
                file_size_mb = photo_file.file_size / 1024 / 1024
                raise InvalidFileError(
                    ERROR_MESSAGES["file_too_large"].format(limit=settings.MAX_IMAGE_SIZE_MB),
                    file_size=photo_file.file_size
                )
    
    async def _validate_pdf_file(self, document) -> None:
        """Validate PDF file size and type."""
        # Check MIME type
        if document.mime_type not in SUPPORTED_DOCUMENT_TYPES:
            raise InvalidFileError(
                ERROR_MESSAGES["invalid_file_type"],
                file_type=document.mime_type
            )
        
        # Check file size
        if document.file_size:
            if not self._validate_file_size(document.file_size, settings.MAX_PDF_SIZE_MB):
                file_size_mb = document.file_size / 1024 / 1024
                raise InvalidFileError(
                    ERROR_MESSAGES["file_too_large"].format(limit=settings.MAX_PDF_SIZE_MB),
                    file_size=document.file_size
                )
    
    async def _handle_no_active_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages when no session is active."""
        guidance_message = (
            "🤔 **Tidak ada operasi yang sedang berjalan.**\n\n"
            "Untuk memulai, silakan:\n"
            "📸 Kirim foto KTP/NPWP, atau\n"
            "📄 Kirim file PDF\n\n"
            "💡 Gunakan /help untuk bantuan lengkap."
        )
        
        await update.message.reply_text(
            text=guidance_message,
            parse_mode='Markdown'
        )
    
    async def _handle_pdf_naming(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle PDF file naming input."""
        file_name = update.message.text.strip()
        
        # Validate filename
        if len(file_name) < 2:
            await update.message.reply_text(
                "❌ Nama file terlalu pendek. Masukkan minimal 2 karakter."
            )
            return
        
        if len(file_name) > 100:
            await update.message.reply_text(
                "❌ Nama file terlalu panjang. Maksimal 100 karakter."
            )
            return
        
        # Store filename and proceed to save
        self._set_session_data(context, 'custom_filename', file_name)
        self._set_session_state(context, 'saving_pdf')
        
        await update.message.reply_text(
            "✅ Nama file diatur. Menyimpan ke Google Drive...",
            parse_mode='Markdown'
        )
        
        # Import and call PDF save service
        try:
            from services.google_service import GoogleService
            google_service = GoogleService()
            
            result = await google_service.save_pdf_to_drive(context)
            
            if result.get("status") == "success":
                branch = self._get_session_data(context, 'branch', 'N/A')
                success_message = (
                    "✅ **PDF berhasil disimpan!**\n\n"
                    f"📁 **Lokasi**: Cabang {branch} / Folder PDF\n"
                    f"📄 **Nama file**: {file_name}\n\n"
                    "Terima kasih! Silakan kirim file lain jika diperlukan."
                )
                
                await update.message.reply_text(
                    text=success_message,
                    parse_mode='Markdown'
                )
            else:
                error_msg = result.get('message', 'Terjadi kesalahan tidak diketahui')
                await update.message.reply_text(f"❌ Gagal menyimpan PDF: {error_msg}")
                
        except Exception as save_error:
            self.logger.error(f"Error saving PDF: {save_error}")
            await update.message.reply_text(
                "❌ Terjadi kesalahan saat menyimpan PDF. Silakan coba lagi."
            )
        
        # Clear session after completion
        self._clear_user_session(context)
    
    async def _handle_data_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle data editing input."""
        new_value = update.message.text.strip()
        edit_field = self._get_session_data(context, 'edit_field')
        
        if not edit_field:
            await update.message.reply_text(
                "❌ Tidak ada field yang sedang diedit. Silakan mulai ulang."
            )
            self._clear_user_session(context)
            return
        
        # Validate new value based on field type
        validation_error = await self._validate_edit_value(edit_field, new_value)
        if validation_error:
            await update.message.reply_text(f"❌ {validation_error}")
            return
        
        # FIXED: Update BOTH extracted_data dict AND document_data object
        extracted_data = self._get_session_data(context, 'extracted_data', {})
        document_data_obj = self._get_session_data(context, 'document_data')
        
        # Update dict
        extracted_data[edit_field] = new_value
        self._set_session_data(context, 'extracted_data', extracted_data)
        
        # Update DocumentData object if it exists
        if document_data_obj:
            setattr(document_data_obj, edit_field, new_value)
            self._set_session_data(context, 'document_data', document_data_obj)
        
        # Remove edit-related session data
        self._set_session_data(context, 'edit_field', None)
        
        # Delete the previous messages for cleaner UI
        try:
            last_bot_message_id = self._get_session_data(context, 'last_bot_message_id')
            if last_bot_message_id:
                await self._delete_message_safely(
                    context, 
                    update.effective_chat.id, 
                    last_bot_message_id
                )
            
            await self._delete_message_safely(
                context,
                update.effective_chat.id,
                update.message.message_id
            )
        except Exception:
            pass  # Ignore deletion errors
        
        # Generate new preview and send
        from services.data_service import DataService
        data_service = DataService()
        
        # FIXED: Use DocumentData object for preview if available
        preview_data = document_data_obj if document_data_obj else extracted_data
        
        preview_text = data_service.build_preview_text(
            preview_data,
            self._get_session_data(context, 'branch'),
            self._get_session_data(context, 'sheet_name'),
            self._get_session_data(context, 'nama_toko', '')
        )
        
        from utils.keyboards import get_confirmation_keyboard
        
        new_message = await update.message.reply_text(
            text=preview_text,
            reply_markup=get_confirmation_keyboard(),
            parse_mode='HTML'
        )
        
        # Store new message ID and update state
        self._set_session_data(context, 'last_bot_message_id', new_message.message_id)
        self._set_session_state(context, 'awaiting_confirmation')
    
    async def _handle_unexpected_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle unexpected text messages during workflow."""
        current_state = self._get_session_state(context)
        workflow_type = self._get_session_data(context, 'workflow_type')
        
        help_message = (
            f"🤔 **Pesan tidak dimengerti**\n\n"
            f"Workflow aktif: {workflow_type}\n"
            f"State saat ini: {current_state}\n\n"
            "Silakan gunakan tombol yang tersedia atau ketik /cancel untuk membatalkan."
        )
        
        await update.message.reply_text(
            text=help_message,
            parse_mode='Markdown'
        )
    
    async def _validate_edit_value(self, field: str, value: str) -> str:
        """
        Validate edited value based on field type.
        Returns error message if invalid, None if valid.
        """
        if not value.strip():
            return "Nilai tidak boleh kosong"
        
        # Import validators
        from core.validators import DocumentValidator
        
        try:
            if field == 'nama':
                is_valid, error = DocumentValidator.validate_nama(value)
                if not is_valid:
                    return error
                    
            elif field == 'alamat':
                is_valid, error = DocumentValidator.validate_alamat(value)
                if not is_valid:
                    return error
                    
            elif field == 'nik':
                is_valid, error = DocumentValidator.validate_nik(value)
                if not is_valid:
                    return error
                    
            elif field == 'npwp_15':
                is_valid, error = DocumentValidator.validate_npwp_15(value)
                if not is_valid:
                    return error
                    
            elif field == 'npwp_16':
                is_valid, error = DocumentValidator.validate_npwp_16(value)
                if not is_valid:
                    return error
            
            return None  # Valid
            
        except Exception as e:
            self.logger.error(f"Error validating edit value: {e}")
            return "Terjadi kesalahan saat validasi"
    
    async def handle_unsupported_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle unsupported message types (stickers, voice, etc.).
        """
        try:
            self._log_user_action(update, "unsupported_message", {
                "message_type": type(update.message).__name__
            })
            
            unsupported_message = (
                "❌ **Tipe pesan tidak didukung**\n\n"
                "Bot ini hanya menerima:\n"
                "📸 Foto (JPG/PNG) untuk KTP/NPWP\n"
                "📄 File PDF untuk arsip\n"
                "💬 Pesan teks untuk input data\n\n"
                "Silakan kirim foto atau PDF untuk memulai."
            )
            
            await update.message.reply_text(
                text=unsupported_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)