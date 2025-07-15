"""
Telegram inline keyboard utilities.
Provides various keyboards for user interactions with improved UX.
"""

from typing import List, Dict, Any, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import settings


def get_branch_keyboard() -> InlineKeyboardMarkup:
    """
    Create keyboard with branch selection buttons.
    Organized in a clean layout for better UX.
    
    Returns:
        InlineKeyboardMarkup for branch selection
    """
    keyboard = []
    branches = sorted(settings.get_branch_list())
    
    # Group branches in rows of 2 for better mobile experience
    for i in range(0, len(branches), 2):
        row = []
        
        # Add first branch in the row
        branch = branches[i]
        row.append(InlineKeyboardButton(
            f"🏢 {branch}", 
            callback_data=f"branch_{branch}"
        ))
        
        # Add second branch if exists
        if i + 1 < len(branches):
            branch = branches[i + 1]
            row.append(InlineKeyboardButton(
                f"🏢 {branch}", 
                callback_data=f"branch_{branch}"
            ))
        
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Create confirmation keyboard with save, edit, and cancel options.
    
    Returns:
        InlineKeyboardMarkup for confirmation actions
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Simpan", callback_data="confirm_save"),
            InlineKeyboardButton("✏️ Edit", callback_data="confirm_edit")
        ],
        [
            InlineKeyboardButton("❌ Batal", callback_data="cancel_op")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_npwp_type_keyboard() -> InlineKeyboardMarkup:
    """
    Create keyboard for NPWP type selection (company/personal).
    
    Returns:
        InlineKeyboardMarkup for NPWP type selection
    """
    keyboard = [
        [
            InlineKeyboardButton("🏢 Perusahaan", callback_data="npwptype_company"),
            InlineKeyboardButton("👤 Orang Pribadi", callback_data="npwptype_personal")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_edit_keyboard(available_fields: List[Dict[str, str]]) -> InlineKeyboardMarkup:
    """
    Create dynamic edit keyboard based on available fields.
    
    Args:
        available_fields: List of field dictionaries with 'field' and 'display' keys
        
    Returns:
        InlineKeyboardMarkup for field editing
    """
    keyboard = []
    
    # Add field edit buttons (2 per row for better layout)
    for i in range(0, len(available_fields), 2):
        row = []
        
        # First field
        field = available_fields[i]
        row.append(InlineKeyboardButton(
            f"📝 {field['display']}", 
            callback_data=f"edit_{field['field']}"
        ))
        
        # Second field if exists
        if i + 1 < len(available_fields):
            field = available_fields[i + 1]
            row.append(InlineKeyboardButton(
                f"📝 {field['display']}", 
                callback_data=f"edit_{field['field']}"
            ))
        
        keyboard.append(row)
    
    # Add location edit button (full width)
    keyboard.append([
        InlineKeyboardButton("📍 Ubah Lokasi Simpan", callback_data="edit_location")
    ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 Kembali", callback_data="cancel_edit")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_duplicate_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Create keyboard for duplicate data confirmation.
    
    Returns:
        InlineKeyboardMarkup for duplicate confirmation
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Lanjut Simpan", callback_data="force_save"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel_op")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """
    Create admin control keyboard (for future admin features).
    
    Returns:
        InlineKeyboardMarkup for admin actions
    """
    keyboard = [
        [
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("🔧 Settings", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("📋 Logs", callback_data="admin_logs")
        ],
        [
            InlineKeyboardButton("🔄 Restart", callback_data="admin_restart"),
            InlineKeyboardButton("❌ Close", callback_data="admin_close")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, 
                          prefix: str = "page") -> InlineKeyboardMarkup:
    """
    Create pagination keyboard for navigating through pages.
    
    Args:
        current_page: Current page number (0-indexed)
        total_pages: Total number of pages
        prefix: Callback data prefix
        
    Returns:
        InlineKeyboardMarkup for pagination
    """
    keyboard = []
    
    if total_pages <= 1:
        return InlineKeyboardMarkup(keyboard)
    
    row = []
    
    # Previous button
    if current_page > 0:
        row.append(InlineKeyboardButton(
            "⬅️ Prev", 
            callback_data=f"{prefix}_{current_page - 1}"
        ))
    
    # Page indicator
    row.append(InlineKeyboardButton(
        f"{current_page + 1}/{total_pages}", 
        callback_data="noop"
    ))
    
    # Next button
    if current_page < total_pages - 1:
        row.append(InlineKeyboardButton(
            "Next ➡️", 
            callback_data=f"{prefix}_{current_page + 1}"
        ))
    
    keyboard.append(row)
    
    # Jump to first/last for large page counts
    if total_pages > 5:
        jump_row = []
        
        if current_page > 2:
            jump_row.append(InlineKeyboardButton(
                "⏮️ First", 
                callback_data=f"{prefix}_0"
            ))
        
        if current_page < total_pages - 3:
            jump_row.append(InlineKeyboardButton(
                "Last ⏭️", 
                callback_data=f"{prefix}_{total_pages - 1}"
            ))
        
        if jump_row:
            keyboard.append(jump_row)
    
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(yes_data: str = "confirm_yes", 
                       no_data: str = "confirm_no") -> InlineKeyboardMarkup:
    """
    Create simple yes/no confirmation keyboard.
    
    Args:
        yes_data: Callback data for yes button
        no_data: Callback data for no button
        
    Returns:
        InlineKeyboardMarkup for yes/no confirmation
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Ya", callback_data=yes_data),
            InlineKeyboardButton("❌ Tidak", callback_data=no_data)
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_menu_keyboard(menu_items: List[Dict[str, str]], 
                     columns: int = 2) -> InlineKeyboardMarkup:
    """
    Create dynamic menu keyboard from list of items.
    
    Args:
        menu_items: List of menu item dictionaries with 'text' and 'callback_data'
        columns: Number of columns in the keyboard layout
        
    Returns:
        InlineKeyboardMarkup for menu navigation
    """
    keyboard = []
    
    # Group items into rows
    for i in range(0, len(menu_items), columns):
        row = []
        
        for j in range(columns):
            if i + j < len(menu_items):
                item = menu_items[i + j]
                row.append(InlineKeyboardButton(
                    item['text'], 
                    callback_data=item['callback_data']
                ))
        
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


def create_url_keyboard(text: str, url: str) -> InlineKeyboardMarkup:
    """
    Create keyboard with a single URL button.
    
    Args:
        text: Button text
        url: Target URL
        
    Returns:
        InlineKeyboardMarkup with URL button
    """
    keyboard = [
        [InlineKeyboardButton(text, url=url)]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def combine_keyboards(*keyboards: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """
    Combine multiple keyboards into one.
    
    Args:
        keyboards: Multiple InlineKeyboardMarkup objects to combine
        
    Returns:
        Combined InlineKeyboardMarkup
    """
    combined_keyboard = []
    
    for keyboard in keyboards:
        if keyboard and keyboard.inline_keyboard:
            combined_keyboard.extend(keyboard.inline_keyboard)
    
    return InlineKeyboardMarkup(combined_keyboard)


def add_cancel_button(keyboard: InlineKeyboardMarkup, 
                     cancel_text: str = "❌ Batal",
                     cancel_data: str = "cancel_op") -> InlineKeyboardMarkup:
    """
    Add cancel button to existing keyboard.
    
    Args:
        keyboard: Existing keyboard
        cancel_text: Cancel button text
        cancel_data: Cancel button callback data
        
    Returns:
        Keyboard with cancel button added
    """
    new_keyboard = list(keyboard.inline_keyboard)
    new_keyboard.append([
        InlineKeyboardButton(cancel_text, callback_data=cancel_data)
    ])
    
    return InlineKeyboardMarkup(new_keyboard)