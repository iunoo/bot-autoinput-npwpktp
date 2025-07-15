"""
Callback query handlers for the Telegram bot.
Handles inline keyboard button presses and user interactions.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from .base import BaseHandler
from config.settings import settings
from config.constants import ERROR_MESSAGES
from core.exceptions import ValidationError, DuplicateDataError


class CallbackHandlers(BaseHandler):
    """
    Handler class for callback queries (inline keyboard button presses).
    """
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Main callback query handler that routes to specific handlers.
        """
        try:
            query = update.callback_query
            await query.answer()  # Acknowledge the callback
            
            callback_data = query.data
            current_state = self._get_session_state(context)
            
            # Log user action
            self._log_user_action(update, "callback_query", {
                "callback_data": callback_data,
                "current_state": current_state
            })
            
            # Route to specific handlers based on callback data
            if callback_data.startswith("branch_"):
                await self._handle_branch_selection(update, context)
            elif callback_data.startswith("npwptype_"):
                await self._handle_npwp_type_selection(update, context)
            elif callback_data == "confirm_save":
                await self._handle_save_confirmation(update, context)
            elif callback_data == "confirm_edit":
                await self._handle_edit_request(update, context)
            elif callback_data.startswith("edit_"):
                await self._handle_field_edit(update, context)
            elif callback_data == "cancel_edit":
                await self._handle_cancel_edit(update, context)
            elif callback_data == "cancel_op":
                await self._handle_cancel_operation(update, context)
            elif callback_data == "force_save":
                await self._handle_force_save(update, context)
            else:
                await self._handle_unknown_callback(update, context)
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def _handle_branch_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle branch selection from inline keyboard."""
        query = update.callback_query
        branch_code = query.data.split("_")[1]
        
        # Validate branch code
        if not settings.is_valid_branch(branch_code):
            await query.edit_message_text(
                text=ERROR_MESSAGES["invalid_branch"]
            )
            return
        
        # Store branch information
        self._set_session_data(context, 'branch', branch_code)
        self._set_session_data(context, 'sheet_name', settings.SHEET_NAME_MAP[branch_code])
        
        current_state = self._get_session_state(context)
        workflow_type = self._get_session_data(context, 'workflow_type')
        
        # Handle based on current state and workflow
        if current_state == 'awaiting_branch_edit':
            # User is editing branch after preview
            await self._return_to_preview(update, context)
        elif workflow_type == 'photo':
            await self._process_photo_workflow(update, context)
        elif workflow_type == 'pdf':
            await self._process_pdf_workflow(update, context)
        else:
            await query.edit_message_text(
                text="❌ Workflow tidak dikenali. Silakan mulai ulang."
            )
            self._clear_user_session(context)
    
    async def _handle_npwp_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle NPWP type selection (company/personal)."""
        query = update.callback_query
        npwp_type = query.data.split("_")[1]  # company or personal
        
        self._set_session_data(context, 'npwp_type', npwp_type)
        
        # Process the document data and show preview
        await self._process_document_and_show_preview(update, context)
    
    async def _handle_save_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle save confirmation."""
        query = update.callback_query
        
        await query.edit_message_text(
            text="💾 Menyimpan data...",
            parse_mode='Markdown'
        )
        
        try:
            # Import services
            from services.google_service import GoogleService
            google_service = GoogleService()
            
            # Save photo and data
            result = await google_service.save_photo_and_data(
                context.bot, 
                context.user_data,
                bypass_duplicate_check=False
            )
            
            await self._handle_save_result(update, context, result)
            
        except DuplicateDataError as e:
            await self._handle_duplicate_data(update, context, e)
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Gagal menyimpan: {str(e)}"
            )
            self._clear_user_session(context)
    
    async def _handle_edit_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle edit request - show edit options."""
        query = update.callback_query
        
        # Get available fields for editing
        extracted_data = self._get_session_data(context, 'extracted_data', {})
        
        keyboard = []
        
        # Field mapping for display
        field_map = {
            "document_type": "📇 Tipe Dokumen",
            "nama": "👤 Nama",
            "alamat": "🏠 Alamat",
            "nik": "🔢 NIK",
            "npwp_15": "🔢 NPWP 15",
            "npwp_16": "🔢 NPWP 16"
        }
        
        # Add edit buttons for available fields
        for field, display_name in field_map.items():
            if field in extracted_data and extracted_data[field]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"Ubah: {display_name}", 
                        callback_data=f"edit_{field}"
                    )
                ])
        
        # Add edit location button
        keyboard.append([
            InlineKeyboardButton(
                "📍 Ubah Lokasi Simpan", 
                callback_data="edit_location"
            )
        ])
        
        # Add back button
        keyboard.append([
            InlineKeyboardButton(
                "🔙 Kembali", 
                callback_data="cancel_edit"
            )
        ])
        
        await query.edit_message_text(
            text=query.message.text + "\n\n---\n📝 Pilih data yang ingin diubah:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        self._set_session_state(context, 'selecting_edit_field')
    
    async def _handle_field_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle specific field edit request."""
        query = update.callback_query
        callback_data = query.data
        
        if callback_data == "edit_location":
            # Handle location edit
            from utils.keyboards import get_branch_keyboard
            
            await query.edit_message_text(
                text="📍 Silakan pilih lokasi penyimpanan yang baru:",
                reply_markup=get_branch_keyboard()
            )
            self._set_session_state(context, 'awaiting_branch_edit')
            
        else:
            # Handle field edit
            field_name = callback_data.split("_", 1)[1]
            
            # Field display names
            display_names = {
                "document_type": "Tipe Dokumen",
                "nama": "Nama", 
                "alamat": "Alamat",
                "nik": "NIK",
                "npwp_15": "NPWP 15",
                "npwp_16": "NPWP 16"
            }
            
            display_name = display_names.get(field_name, field_name)
            
            edit_message = (
                f"✍️ **Mengubah: {display_name}**\n\n"
                f"Silakan kirimkan nilai baru untuk {display_name.lower()}:"
            )
            
            new_message = await query.edit_message_text(
                text=edit_message,
                parse_mode='Markdown'
            )
            
            # Store edit context
            self._set_session_data(context, 'edit_field', field_name)
            self._set_session_data(context, 'last_bot_message_id', new_message.message_id)
            self._set_session_state(context, 'awaiting_edit_input')
    
    async def _handle_cancel_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle cancel edit - return to preview."""
        await self._return_to_preview(update, context)
    
    async def _handle_cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle operation cancellation."""
        query = update.callback_query
        
        await query.edit_message_text(
            text="❌ Operasi dibatalkan.\n\nSilakan kirim foto atau file baru untuk memulai ulang."
        )
        
        self._clear_user_session(context)
    
    async def _handle_force_save(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle force save (bypass duplicate check)."""
        query = update.callback_query
        
        await query.edit_message_text(
            text="💾 Menyimpan data (mengabaikan duplikat)...",
            parse_mode='Markdown'
        )
        
        try:
            from services.google_service import GoogleService
            google_service = GoogleService()
            
            result = await google_service.save_photo_and_data(
                context.bot,
                context.user_data, 
                bypass_duplicate_check=True
            )
            
            await self._handle_save_result(update, context, result)
            
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Gagal menyimpan: {str(e)}"
            )
            self._clear_user_session(context)
    
    async def _handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle unknown callback data."""
        query = update.callback_query
        
        await query.edit_message_text(
            text="❌ Aksi tidak dikenali. Silakan mulai ulang dengan /start"
        )
        
        self._clear_user_session(context)
    
    async def _process_photo_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process photo workflow after branch selection."""
        query = update.callback_query
        
        await query.edit_message_text(
            text="🧠 Memproses gambar dengan AI...",
            parse_mode='Markdown'
        )
        
        try:
            # Import AI service
            from services.ai_service import AIService
            ai_service = AIService()
            
            # Get file and extract data
            file_id = self._get_session_data(context, 'file_id')
            file_tg = await context.bot.get_file(file_id)
            file_bytes = await file_tg.download_as_bytearray()
            
            # Extract data using AI
            document_data = await ai_service.extract_document_data(file_bytes)
            
            if not document_data:
                await query.edit_message_text(
                    text=ERROR_MESSAGES["ai_processing_failed"]
                )
                self._clear_user_session(context)
                return
            
            # Store extracted data
            self._set_session_data(context, 'document_data', document_data)
            self._set_session_data(context, 'extracted_data', document_data.to_dict())
            
            # Check if NPWP needs type selection
            if document_data.document_type.value == "NPWP":
                from utils.keyboards import get_npwp_type_keyboard
                
                await query.edit_message_text(
                    text="🏢 NPWP terdeteksi. Tentukan jenisnya:",
                    reply_markup=get_npwp_type_keyboard()
                )
                self._set_session_state(context, 'awaiting_npwp_type')
            else:
                # For KTP, proceed directly to preview
                document_data.npwp_type = None
                await self._process_document_and_show_preview(update, context)
                
        except Exception as e:
            self.logger.error(f"Error processing photo: {e}")
            await query.edit_message_text(
                text=ERROR_MESSAGES["ai_processing_failed"]
            )
            self._clear_user_session(context)
    
    async def _process_pdf_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process PDF workflow after branch selection."""
        query = update.callback_query
        
        await query.edit_message_text(
            text="📝 Silakan ketik nama lengkap untuk file PDF ini:",
            parse_mode='Markdown'
        )
        
        self._set_session_state(context, 'awaiting_pdf_name')
    
    async def _process_document_and_show_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process document data and show preview."""
        try:
            # Import services
            from services.data_service import DataService
            data_service = DataService()
            
            # Get data from session
            extracted_data = self._get_session_data(context, 'extracted_data')
            document_data_obj = self._get_session_data(context, 'document_data')  # This is the DocumentData object
            branch = self._get_session_data(context, 'branch')
            sheet_name = self._get_session_data(context, 'sheet_name')
            nama_toko = self._get_session_data(context, 'nama_toko', '')
            
            # Handle NPWP type if selected
            npwp_type = self._get_session_data(context, 'npwp_type')
            if npwp_type and document_data_obj:
                from models.document import NPWPType
                document_data_obj.npwp_type = NPWPType(npwp_type)
                # Also update the extracted_data dict
                extracted_data['npwp_type'] = npwp_type
                self._set_session_data(context, 'extracted_data', extracted_data)
            
            # FIXED: Use DocumentData object if available, otherwise use extracted_data dict
            preview_data = document_data_obj if document_data_obj else extracted_data
            
            # Build preview using the correct data type
            preview_text = data_service.build_preview_text(
                preview_data, branch, sheet_name, nama_toko
            )
            
            from utils.keyboards import get_confirmation_keyboard
            
            await update.callback_query.edit_message_text(
                text=preview_text,
                reply_markup=get_confirmation_keyboard(),
                parse_mode='HTML'
            )
            
            self._set_session_state(context, 'awaiting_confirmation')
            
        except Exception as e:
            self.logger.error(f"Error showing preview: {e}", exc_info=True)
            await update.callback_query.edit_message_text(
                text="❌ Terjadi kesalahan saat memproses data."
            )
            self._clear_user_session(context)
    
    async def _return_to_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Return to document preview after edit."""
        await self._process_document_and_show_preview(update, context)
    
    async def _handle_save_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: dict) -> None:
        """Handle the result of save operation."""
        query = update.callback_query
        
        if result.get("status") == "success":
            # Build success message
            document_data = self._get_session_data(context, 'document_data')
            branch = self._get_session_data(context, 'branch')
            
            success_message = (
                "✅ **Berhasil disimpan!**\n\n"
                f"📋 **Dokumen**: {document_data.document_type.value}\n"
                f"👤 **Nama**: {document_data.nama}\n"
                f"📍 **Cabang**: {branch}\n\n"
                "📝 Data telah ditambahkan ke spreadsheet\n"
                "📁 File telah diarsipkan ke Google Drive\n\n"
                "Terima kasih! Silakan kirim dokumen lain jika diperlukan."
            )
            
            await query.edit_message_text(
                text=success_message,
                parse_mode='Markdown'
            )
            
        elif result.get("status") == "duplicate_found":
            await self._handle_duplicate_data(update, context, None)
        else:
            error_msg = result.get('message', 'Terjadi kesalahan tidak diketahui')
            await query.edit_message_text(
                text=f"❌ Gagal menyimpan: {error_msg}"
            )
        
        # Clear session after completion
        self._clear_user_session(context)
    
    async def _handle_duplicate_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   exception: DuplicateDataError = None) -> None:
        """Handle duplicate data detection."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Lanjut Simpan", callback_data="force_save"),
                InlineKeyboardButton("❌ Batal", callback_data="cancel_op")
            ]
        ]
        
        await update.callback_query.edit_message_text(
            text="⚠️ **PERINGATAN: Data Duplikat**\n\nNIK/NPWP ini sudah ada di database. Tetap simpan?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        self._set_session_state(context, 'awaiting_duplicate_confirmation')