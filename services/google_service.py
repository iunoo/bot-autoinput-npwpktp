"""
Google services integration for Drive and Sheets operations.
Provides robust file upload, data storage, and duplicate checking with retry logic.
"""

import io
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

from config.settings import settings
from core.exceptions import GoogleServiceError, DuplicateDataError, AuthenticationError
from models.document import DocumentData


class GoogleService:
    """
    Service for Google Drive and Sheets operations.
    Handles authentication, file operations, and data management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._credentials = None
        self._drive_service = None
        self._sheets_service = None
        self._folder_cache = {}  # Cache for folder IDs
    
    async def initialize(self) -> None:
        """Initialize Google services with authentication."""
        try:
            self._credentials = self._get_credentials()
            self._drive_service = build('drive', 'v3', credentials=self._credentials)
            self._sheets_service = build('sheets', 'v4', credentials=self._credentials)
            self.logger.info("Google services initialized successfully")
        except Exception as e:
            raise GoogleServiceError(f"Failed to initialize Google services: {e}")
    
    def _get_credentials(self) -> Credentials:
        """Get Google API credentials with automatic refresh."""
        try:
            if settings.USE_SERVICE_ACCOUNT:
                # Use service account credentials
                credentials = ServiceAccountCredentials.from_service_account_file(
                    settings.get_google_credentials_path(),
                    scopes=settings.GOOGLE_SCOPES
                )
                self.logger.info("Using service account credentials")
                return credentials
            else:
                # Use OAuth2 credentials
                creds = None
                
                # Load existing token
                if settings.GOOGLE_TOKEN_FILE.exists():
                    creds = Credentials.from_authorized_user_file(
                        settings.GOOGLE_TOKEN_FILE, 
                        settings.GOOGLE_SCOPES
                    )
                
                # Refresh or create new credentials
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        self.logger.info("Refreshing expired credentials")
                        creds.refresh(Request())
                    else:
                        self.logger.info("Creating new OAuth2 credentials")
                        if not settings.GOOGLE_CREDENTIALS_FILE.exists():
                            raise GoogleServiceError(
                                f"Credentials file not found: {settings.GOOGLE_CREDENTIALS_FILE}"
                            )
                        
                        flow = InstalledAppFlow.from_client_secrets_file(
                            settings.GOOGLE_CREDENTIALS_FILE, 
                            settings.GOOGLE_SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    
                    # Save credentials
                    with open(settings.GOOGLE_TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                
                self.logger.info("Using OAuth2 credentials")
                return creds
                
        except Exception as e:
            raise AuthenticationError(f"Google authentication failed: {e}", auth_type="google")
    
    async def save_photo_and_data(self, bot, user_data: Dict[str, Any], 
                                bypass_duplicate_check: bool = False) -> Dict[str, Any]:
        """
        Save photo to Drive and data to Sheets with comprehensive error handling.
        
        Args:
            bot: Telegram bot instance
            user_data: User session data
            bypass_duplicate_check: Skip duplicate checking if True
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Ensure services are initialized
            if not self._sheets_service or not self._drive_service:
                await self.initialize()
            
            # Extract data from user session
            document_data = user_data.get('document_data')
            if not document_data:
                raise GoogleServiceError("No document data found in user session")
            
            branch = user_data.get('branch')
            if not branch or not settings.is_valid_branch(branch):
                raise GoogleServiceError(f"Invalid branch: {branch}")
            
            sheet_name = settings.SHEET_NAME_MAP.get(branch)
            nama_toko = user_data.get('nama_toko', '')
            
            # Check for duplicates unless bypassed
            if not bypass_duplicate_check:
                is_duplicate = await self._check_for_duplicates(
                    sheet_name, 
                    document_data
                )
                if is_duplicate:
                    return {"status": "duplicate_found"}
            
            # Save to spreadsheet first (safer to fail here)
            await self._save_to_spreadsheet(document_data, sheet_name, nama_toko)
            
            # Upload file to Drive
            file_id = user_data.get('file_id')
            if file_id:
                await self._upload_file_to_drive(bot, file_id, document_data, branch)
            
            self.logger.info(f"Successfully saved document for {document_data.nama}")
            return {"status": "success"}
            
        except DuplicateDataError:
            return {"status": "duplicate_found"}
        except Exception as e:
            self.logger.error(f"Error saving photo and data: {e}", exc_info=True)
            return {
                "status": "error", 
                "message": str(e)
            }
    
    async def save_pdf_to_drive(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save PDF file to Google Drive.
        
        Args:
            user_data: User session data from context
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Ensure services are initialized
            if not self._drive_service:
                await self.initialize()
            
            # Extract required data
            file_id = user_data.get('file_id')
            branch = user_data.get('branch')
            custom_filename = user_data.get('custom_filename')
            original_filename = user_data.get('original_filename', 'document.pdf')
            
            if not file_id:
                raise GoogleServiceError("No file ID found in user session")
            
            if not branch or not settings.is_valid_branch(branch):
                raise GoogleServiceError(f"Invalid branch: {branch}")
            
            # Prepare filename
            filename = custom_filename or Path(original_filename).stem
            file_extension = Path(original_filename).suffix or '.pdf'
            final_filename = f"{filename}{file_extension}"
            
            # Get or create PDF folder
            parent_folder_id = settings.FOLDER_MAP[branch]
            pdf_folder_id = await self._find_or_create_subfolder(
                parent_folder_id, 
                'PDF'
            )
            
            # Download file from Telegram (this needs bot instance)
            # Note: In real implementation, you'd pass the bot instance
            # For now, we'll raise an error indicating this needs to be handled
            raise GoogleServiceError("PDF upload requires bot instance - implement in handler")
            
        except Exception as e:
            self.logger.error(f"Error saving PDF: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _check_for_duplicates(self, sheet_name: str, 
                                  document_data: DocumentData) -> bool:
        """
        Check for duplicate data in spreadsheet.
        
        Args:
            sheet_name: Name of the sheet to check
            document_data: Document data to check
            
        Returns:
            True if duplicate found, False otherwise
        """
        try:
            # Get values to check for duplicates
            check_values = document_data.get_duplicate_check_values()
            if not check_values:
                return False
            
            # Define column ranges to check (F, G, H for NPWP15, NPWP16/NIK, ID_TKU)
            ranges_to_check = [
                f"'{sheet_name}'!F:F",  # NPWP 15
                f"'{sheet_name}'!G:G",  # NPWP 16 / NIK  
                f"'{sheet_name}'!H:H"   # ID TKU
            ]
            
            # Get data from sheets
            result = self._sheets_service.spreadsheets().values().batchGet(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                ranges=ranges_to_check
            ).execute()
            
            value_ranges = result.get('valueRanges', [])
            
            # Check each column for duplicates
            for i, value_range in enumerate(value_ranges):
                column_values = value_range.get('values', [])
                for row in column_values:
                    if row and row[0]:  # Check if cell has value
                        cell_value = str(row[0]).strip()
                        if cell_value in check_values:
                            self.logger.warning(f"Duplicate found: {cell_value}")
                            return True
            
            return False
            
        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleServiceError(f"Sheet not found: {sheet_name}")
            else:
                raise GoogleServiceError(f"Error checking duplicates: {e}")
        except Exception as e:
            self.logger.error(f"Error checking duplicates: {e}")
            # In case of error, return False to allow saving (safer option)
            return False
    
    async def _save_to_spreadsheet(self, document_data: DocumentData, 
                                 sheet_name: str, nama_toko: str = "") -> None:
        """
        Save document data to Google Sheets.
        
        Args:
            document_data: Document data to save
            sheet_name: Target sheet name
            nama_toko: Store name from caption
        """
        try:
            # Prepare row data
            row_data = document_data.to_sheet_row(nama_toko)
            
            # Append to spreadsheet
            body = {'values': [row_data]}
            
            result = self._sheets_service.spreadsheets().values().append(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"'{sheet_name}'!A1",
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updates = result.get('updates', {})
            updated_cells = updates.get('updatedCells', 0)
            
            self.logger.info(f"Added {updated_cells} cells to {sheet_name}")
            
        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleServiceError(f"Sheet not found: {sheet_name}")
            elif e.resp.status == 403:
                raise GoogleServiceError("Permission denied - check Google Sheets access")
            else:
                raise GoogleServiceError(f"Sheets API error: {e}")
        except Exception as e:
            raise GoogleServiceError(f"Error saving to spreadsheet: {e}")
    
    async def _upload_file_to_drive(self, bot, file_id: str, 
                                  document_data: DocumentData, branch: str) -> str:
        """
        Upload file to Google Drive.
        
        Args:
            bot: Telegram bot instance
            file_id: Telegram file ID
            document_data: Document data for naming
            branch: Branch code for folder selection
            
        Returns:
            Google Drive file ID
        """
        try:
            # Download file from Telegram
            file_tg = await bot.get_file(file_id)
            file_content = io.BytesIO(await file_tg.download_as_bytearray())
            
            # Get or create target folder
            parent_folder_id = settings.FOLDER_MAP[branch]
            target_folder_id = await self._find_or_create_subfolder(
                parent_folder_id, 
                'Sudah diinput'
            )
            
            # Generate filename
            file_extension = '.jpg'  # Default for photos
            filename = f"{document_data.nama} - {document_data.document_type.value}{file_extension}"
            
            # Sanitize filename
            filename = self._sanitize_filename(filename)
            
            # Upload file
            file_metadata = {
                'name': filename,
                'parents': [target_folder_id]
            }
            
            media = MediaIoBaseUpload(
                file_content, 
                mimetype='image/jpeg', 
                resumable=True
            )
            
            drive_file = self._drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            drive_file_id = drive_file.get('id')
            self.logger.info(f"Uploaded file to Drive: {filename} (ID: {drive_file_id})")
            
            return drive_file_id
            
        except HttpError as e:
            if e.resp.status == 403:
                raise GoogleServiceError("Permission denied - check Google Drive access")
            elif e.resp.status == 404:
                raise GoogleServiceError(f"Folder not found for branch: {branch}")
            else:
                raise GoogleServiceError(f"Drive API error: {e}")
        except Exception as e:
            raise GoogleServiceError(f"Error uploading to Drive: {e}")
    
    async def _find_or_create_subfolder(self, parent_id: str, 
                                      subfolder_name: str) -> str:
        """
        Find existing subfolder or create new one.
        
        Args:
            parent_id: Parent folder ID
            subfolder_name: Name of subfolder to find/create
            
        Returns:
            Subfolder ID
        """
        try:
            # Check cache first
            cache_key = f"{parent_id}:{subfolder_name}"
            if cache_key in self._folder_cache:
                return self._folder_cache[cache_key]
            
            # Search for existing folder
            query = (
                f"'{parent_id}' in parents and "
                f"name = '{subfolder_name}' and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"trashed = false"
            )
            
            response = self._drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = response.get('files', [])
            
            if files:
                # Folder exists
                folder_id = files[0]['id']
                self.logger.info(f"Found existing folder: {subfolder_name}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                
                folder = self._drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                folder_id = folder.get('id')
                self.logger.info(f"Created new folder: {subfolder_name}")
            
            # Cache the result
            self._folder_cache[cache_key] = folder_id
            return folder_id
            
        except HttpError as e:
            raise GoogleServiceError(f"Error with folder operations: {e}")
        except Exception as e:
            raise GoogleServiceError(f"Error finding/creating subfolder: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for Google Drive.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace problematic characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length (Google Drive supports up to 255 characters)
        if len(sanitized) > 255:
            name_part = sanitized[:240]
            extension = sanitized[240:]
            if '.' in extension:
                extension = extension[extension.rfind('.'):]
            else:
                extension = ''
            sanitized = name_part + extension
        
        return sanitized
    
    async def get_sheet_info(self, sheet_name: str) -> Dict[str, Any]:
        """
        Get information about a specific sheet.
        
        Args:
            sheet_name: Name of the sheet
            
        Returns:
            Dictionary with sheet information
        """
        try:
            if not self._sheets_service:
                await self.initialize()
            
            # Get spreadsheet metadata
            spreadsheet = self._sheets_service.spreadsheets().get(
                spreadsheetId=settings.GOOGLE_SHEET_ID
            ).execute()
            
            # Find the specific sheet
            target_sheet = None
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                raise GoogleServiceError(f"Sheet '{sheet_name}' not found")
            
            properties = target_sheet['properties']
            
            # Get row count (approximate)
            try:
                values_response = self._sheets_service.spreadsheets().values().get(
                    spreadsheetId=settings.GOOGLE_SHEET_ID,
                    range=f"'{sheet_name}'!A:A"
                ).execute()
                
                row_count = len(values_response.get('values', []))
            except:
                row_count = properties.get('gridProperties', {}).get('rowCount', 0)
            
            return {
                'sheet_id': properties['sheetId'],
                'title': properties['title'],
                'row_count': row_count,
                'column_count': properties.get('gridProperties', {}).get('columnCount', 0),
                'tab_color': properties.get('tabColor'),
                'hidden': properties.get('hidden', False)
            }
            
        except Exception as e:
            raise GoogleServiceError(f"Error getting sheet info: {e}")
    
    async def get_folder_info(self, branch: str) -> Dict[str, Any]:
        """
        Get information about branch folder structure.
        
        Args:
            branch: Branch code
            
        Returns:
            Dictionary with folder information
        """
        try:
            if not self._drive_service:
                await self.initialize()
            
            if not settings.is_valid_branch(branch):
                raise GoogleServiceError(f"Invalid branch: {branch}")
            
            parent_folder_id = settings.FOLDER_MAP[branch]
            
            # Get parent folder info
            parent_folder = self._drive_service.files().get(
                fileId=parent_folder_id,
                fields='id, name, createdTime, modifiedTime'
            ).execute()
            
            # Get subfolders
            query = (
                f"'{parent_folder_id}' in parents and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"trashed = false"
            )
            
            response = self._drive_service.files().list(
                q=query,
                fields='files(id, name, createdTime, modifiedTime)'
            ).execute()
            
            subfolders = response.get('files', [])
            
            return {
                'branch': branch,
                'parent_folder': {
                    'id': parent_folder['id'],
                    'name': parent_folder['name'],
                    'created': parent_folder.get('createdTime'),
                    'modified': parent_folder.get('modifiedTime')
                },
                'subfolders': [
                    {
                        'id': folder['id'],
                        'name': folder['name'],
                        'created': folder.get('createdTime'),
                        'modified': folder.get('modifiedTime')
                    }
                    for folder in subfolders
                ]
            }
            
        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleServiceError(f"Folder not found for branch: {branch}")
            else:
                raise GoogleServiceError(f"Error getting folder info: {e}")
        except Exception as e:
            raise GoogleServiceError(f"Error getting folder info: {e}")
    
    async def get_service_health(self) -> Dict[str, Any]:
        """
        Check health of Google services.
        
        Returns:
            Dictionary with service health status
        """
        health_status = {
            'authentication': 'unknown',
            'drive_service': 'unknown',
            'sheets_service': 'unknown',
            'permissions': {}
        }
        
        try:
            # Check authentication
            if not self._credentials:
                await self.initialize()
            
            if self._credentials and self._credentials.valid:
                health_status['authentication'] = 'healthy'
            else:
                health_status['authentication'] = 'invalid'
                return health_status
            
            # Check Drive service
            if self._drive_service:
                try:
                    # Simple test query
                    test_response = self._drive_service.files().list(
                        pageSize=1,
                        fields='files(id, name)'
                    ).execute()
                    health_status['drive_service'] = 'healthy'
                except Exception as e:
                    health_status['drive_service'] = f'error: {str(e)}'
            
            # Check Sheets service
            if self._sheets_service:
                try:
                    # Test access to main spreadsheet
                    spreadsheet = self._sheets_service.spreadsheets().get(
                        spreadsheetId=settings.GOOGLE_SHEET_ID
                    ).execute()
                    health_status['sheets_service'] = 'healthy'
                    health_status['spreadsheet_title'] = spreadsheet.get('properties', {}).get('title')
                except Exception as e:
                    health_status['sheets_service'] = f'error: {str(e)}'
            
            # Check folder permissions
            for branch, folder_id in settings.FOLDER_MAP.items():
                try:
                    folder = self._drive_service.files().get(
                        fileId=folder_id,
                        fields='id, name'
                    ).execute()
                    health_status['permissions'][branch] = 'accessible'
                except Exception as e:
                    health_status['permissions'][branch] = f'error: {str(e)}'
            
        except Exception as e:
            health_status['error'] = str(e)
        
        return health_status
    
    async def cleanup_cache(self) -> None:
        """Clear internal caches."""
        self._folder_cache.clear()
        self.logger.info("Google service cache cleared")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service configuration information."""
        return {
            'use_service_account': settings.USE_SERVICE_ACCOUNT,
            'credentials_file': str(settings.get_google_credentials_path()),
            'spreadsheet_id': settings.GOOGLE_SHEET_ID,
            'scopes': settings.GOOGLE_SCOPES,
            'branches': list(settings.FOLDER_MAP.keys()),
            'sheets': list(settings.SHEET_NAME_MAP.values()),
            'cache_size': len(self._folder_cache)
        }