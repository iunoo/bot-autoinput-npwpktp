"""
Data service for processing, formatting, and validating document data.
Provides business logic for data transformation and presentation.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from models.document import DocumentData, DocumentType, NPWPType
from core.validators import DocumentValidator
from core.exceptions import ValidationError
from config.settings import settings


class DataService:
    """
    Service for data processing, formatting, and business logic operations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_npwp_15(self, npwp: str) -> str:
        """
        Format NPWP 15 digit with proper separators.
        Format: xx.xxx.xxx.x-xxx.xxx
        
        Args:
            npwp: NPWP 15 digit string
            
        Returns:
            Formatted NPWP string
        """
        if not npwp or len(npwp) != 15:
            return npwp or ""
        
        return f"{npwp[0:2]}.{npwp[2:5]}.{npwp[5:8]}.{npwp[8:9]}-{npwp[9:12]}.{npwp[12:15]}"
    
    def format_id_16_digit(self, id_number: str) -> str:
        """
        Format 16-digit ID (NIK/NPWP) with spaces.
        Format: xxxx xxxx xxxx xxxx
        
        Args:
            id_number: 16 digit ID string
            
        Returns:
            Formatted ID string
        """
        if not id_number or len(id_number) != 16:
            return id_number or ""
        
        return f"{id_number[0:4]} {id_number[4:8]} {id_number[8:12]} {id_number[12:16]}"
    
    def build_preview_text(self, document_data, branch: str, 
                          sheet_name: str, nama_toko: str = "") -> str:
        """
        Build comprehensive preview text for user confirmation.
        
        Args:
            document_data: DocumentData object OR dict with extracted data
            branch: Selected branch
            sheet_name: Target sheet name
            nama_toko: Store name from caption
            
        Returns:
            Formatted HTML preview text
        """
        try:
            # FIXED: Handle both DocumentData object and dict
            if isinstance(document_data, dict):
                # Convert dict to DocumentData object
                doc_type = DocumentType(document_data.get('document_type', 'KTP').upper())
                
                document_obj = DocumentData(
                    document_type=doc_type,
                    nama=document_data.get('nama', ''),
                    alamat=document_data.get('alamat'),
                    nik=document_data.get('nik'),
                    npwp_15=document_data.get('npwp_15'),
                    npwp_16=document_data.get('npwp_16')
                )
                
                # Set NPWP type if available
                if 'npwp_type' in document_data and document_data['npwp_type']:
                    document_obj.npwp_type = NPWPType(document_data['npwp_type'])
                    
            else:
                # It's already a DocumentData object
                document_obj = document_data
            
            preview_lines = [
                "🔎 <b>Mohon periksa kembali data dari AI:</b>\n",
                f"📍 <b>Lokasi Simpan</b>",
                f"Cabang: {branch}",
                f"Sheet: {sheet_name}\n"
            ]
            
            # Add store name if available
            if nama_toko:
                preview_lines.extend([
                    f"🏬 <b>Nama Toko (dari caption)</b>",
                    f"{nama_toko}\n"
                ])
            
            preview_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # Document type with NPWP type specification
            doc_display = document_obj.display_name
            preview_lines.extend([
                f"📇 <b>Tipe Dokumen</b>:",
                f"{doc_display}\n"
            ])
            
            # Name
            preview_lines.extend([
                f"👤 <b>Nama</b>:",
                f"{document_obj.nama}\n"
            ])
            
            # Document-specific ID numbers
            if document_obj.document_type == DocumentType.KTP and document_obj.nik:
                formatted_nik = self.format_id_16_digit(document_obj.nik)
                preview_lines.extend([
                    f"🔢 <b>NIK</b>:",
                    f"<code>{formatted_nik}</code>\n"
                ])
            
            elif document_obj.document_type == DocumentType.NPWP:
                if document_obj.npwp_15:
                    formatted_npwp15 = self.format_npwp_15(document_obj.npwp_15)
                    preview_lines.extend([
                        f"🔢 <b>NPWP 15</b>:",
                        f"<code>{formatted_npwp15}</code>\n"
                    ])
                
                if document_obj.npwp_16:
                    formatted_npwp16 = self.format_id_16_digit(document_obj.npwp_16)
                    preview_lines.extend([
                        f"🔢 <b>NPWP 16</b>:",
                        f"<code>{formatted_npwp16}</code>\n"
                    ])
                
                # Show ID TKU for company NPWP
                if document_obj.id_tku:
                    preview_lines.extend([
                        f"🔑 <b>ID TKU</b>:",
                        f"<code>{document_obj.id_tku}</code>\n"
                    ])
            
            # Address
            if document_obj.alamat:
                # Truncate very long addresses for preview
                alamat_display = document_obj.alamat
                if len(alamat_display) > 200:
                    alamat_display = alamat_display[:200] + "..."
                
                preview_lines.extend([
                    f"🏠 <b>Alamat</b>:",
                    f"{alamat_display}\n"
                ])
            
            # Add confidence indicator if available
            if hasattr(document_obj, 'confidence_score') and document_obj.confidence_score:
                confidence_emoji = "🟢" if document_obj.confidence_score > 0.8 else "🟡" if document_obj.confidence_score > 0.6 else "🔴"
                preview_lines.extend([
                    f"{confidence_emoji} <b>Confidence</b>: {document_obj.confidence_score:.1%}\n"
                ])
            
            preview_lines.append("Apakah data di atas sudah benar?")
            
            return "\n".join(preview_lines)
            
        except Exception as e:
            self.logger.error(f"Error building preview text: {e}", exc_info=True)
            return "❌ Error membangun preview data. Silakan coba lagi."
    
    def build_success_message(self, document_data: DocumentData, branch: str, 
                            nama_toko: str = "") -> str:
        """
        Build success message after successful save operation.
        
        Args:
            document_data: Saved document data
            branch: Branch where data was saved
            nama_toko: Store name if any
            
        Returns:
            Formatted success message
        """
        try:
            # Basic info
            doc_display = document_data.display_name
            primary_id = document_data.formatted_primary_id
            id_label = "NIK" if document_data.document_type == DocumentType.KTP else "NPWP"
            sheet_name = settings.SHEET_NAME_MAP.get(branch, branch)
            
            success_lines = [
                "✅ <b>Berhasil disimpan!</b>\n",
                f"📋 <b>Dokumen</b>: {doc_display}",
                f"👤 <b>Nama</b>: {document_data.nama}",
                f"🔢 <b>{id_label}</b>: <code>{primary_id}</code>"
            ]
            
            # Add store name if available
            if nama_toko:
                success_lines.append(f"🏬 <b>Toko</b>: {nama_toko}")
            
            # Add ID TKU if available
            if document_data.id_tku:
                success_lines.append(f"🔑 <b>ID TKU</b>: <code>{document_data.id_tku}</code>")
            
            success_lines.extend([
                "",
                f"📝 <b>Data ditambahkan ke Sheet</b>:",
                f"<code>{sheet_name}</code>",
                "",
                f"📁 <b>File diarsipkan ke Drive</b>:",
                f"<code>{branch} / Sudah diinput</code>",
                "",
                "Terima kasih! Silakan kirim dokumen lain jika diperlukan."
            ])
            
            return "\n".join(success_lines)
            
        except Exception as e:
            self.logger.error(f"Error building success message: {e}")
            return "✅ Data berhasil disimpan!"
    
    def validate_and_process_ai_data(self, raw_ai_data: Dict[str, Any], 
                                   npwp_type: Optional[str] = None) -> DocumentData:
        """
        Validate and process raw AI data into DocumentData object.
        
        Args:
            raw_ai_data: Raw data from AI extraction
            npwp_type: NPWP type if applicable
            
        Returns:
            Validated DocumentData object
            
        Raises:
            ValidationError: If data validation fails
        """
        try:
            # First validate the raw data structure
            validation_errors = DocumentValidator.validate_document_data(
                raw_ai_data,
                raw_ai_data.get('document_type', '')
            )
            
            if validation_errors:
                raise ValidationError(
                    "Data ekstraksi AI tidak valid",
                    validation_errors=validation_errors
                )
            
            # Create DocumentData object
            doc_type = DocumentType(raw_ai_data['document_type'].upper())
            
            document_data = DocumentData(
                document_type=doc_type,
                nama=raw_ai_data['nama'].strip(),
                alamat=raw_ai_data.get('alamat', '').strip() if raw_ai_data.get('alamat') else None,
                nik=raw_ai_data.get('nik'),
                npwp_15=raw_ai_data.get('npwp_15'),
                npwp_16=raw_ai_data.get('npwp_16')
            )
            
            # Set NPWP type if provided and document is NPWP
            if npwp_type and doc_type == DocumentType.NPWP:
                document_data.npwp_type = NPWPType(npwp_type)
            
            # Final completeness check
            completeness_errors = document_data.validate_completeness()
            if completeness_errors:
                raise ValidationError(
                    "Data tidak lengkap",
                    validation_errors=completeness_errors
                )
            
            return document_data
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Error memproses data AI: {str(e)}")
    
    def clean_text_input(self, text: str, field_type: str = "general") -> str:
        """
        Clean and normalize text input based on field type.
        
        Args:
            text: Input text to clean
            field_type: Type of field (nama, alamat, etc.)
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        
        # Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Field-specific cleaning
        if field_type == "nama":
            # Remove special characters but keep common name characters
            cleaned = re.sub(r'[^\w\s\.\'-]', '', cleaned)
            # Proper case for names
            cleaned = ' '.join(word.capitalize() for word in cleaned.split())
        
        elif field_type == "alamat":
            # Keep more characters for addresses
            cleaned = re.sub(r'[^\w\s\.\,\-\/\(\)]', '', cleaned)
            # Capitalize first letter of each word
            cleaned = ' '.join(word.capitalize() for word in cleaned.split())
        
        elif field_type == "numeric":
            # Keep only digits
            cleaned = re.sub(r'\D', '', cleaned)
        
        return cleaned
    
    def generate_filename(self, document_data: DocumentData, 
                         file_extension: str = ".jpg") -> str:
        """
        Generate appropriate filename for document.
        
        Args:
            document_data: Document data
            file_extension: File extension to use
            
        Returns:
            Generated filename
        """
        try:
            # Base filename components
            nama_clean = re.sub(r'[^\w\s]', '', document_data.nama)
            nama_clean = re.sub(r'\s+', '_', nama_clean.strip())
            
            doc_type = document_data.document_type.value
            
            # Add NPWP type specification if applicable
            if document_data.document_type == DocumentType.NPWP and document_data.npwp_type:
                if document_data.npwp_type == NPWPType.COMPANY:
                    doc_type += "_Perusahaan"
                else:
                    doc_type += "_Pribadi"
            
            # Generate filename
            filename = f"{nama_clean}_{doc_type}{file_extension}"
            
            # Ensure filename is not too long
            if len(filename) > 100:
                # Truncate name part
                max_name_length = 100 - len(doc_type) - len(file_extension) - 2
                nama_clean = nama_clean[:max_name_length]
                filename = f"{nama_clean}_{doc_type}{file_extension}"
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error generating filename: {e}")
            return f"Document_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    
    def get_data_summary(self, document_data: DocumentData) -> Dict[str, Any]:
        """
        Get summary statistics and information about document data.
        
        Args:
            document_data: Document data to summarize
            
        Returns:
            Summary dictionary
        """
        summary = {
            'document_type': document_data.document_type.value,
            'has_name': bool(document_data.nama),
            'has_address': bool(document_data.alamat),
            'has_nik': bool(document_data.nik),
            'has_npwp_15': bool(document_data.npwp_15),
            'has_npwp_16': bool(document_data.npwp_16),
            'has_id_tku': bool(document_data.id_tku),
            'npwp_type': document_data.npwp_type.value if document_data.npwp_type else None,
            'primary_id': document_data.primary_id,
            'extraction_timestamp': document_data.extraction_timestamp.isoformat() if hasattr(document_data, 'extraction_timestamp') else None,
            'ai_service_used': getattr(document_data, 'ai_service_used', None)
        }
        
        # Add validation status
        validation_errors = document_data.validate_completeness()
        summary['is_complete'] = len(validation_errors) == 0
        summary['validation_errors'] = validation_errors
        
        # Add character counts
        summary['name_length'] = len(document_data.nama) if document_data.nama else 0
        summary['address_length'] = len(document_data.alamat) if document_data.alamat else 0
        
        return summary
    
    def compare_documents(self, doc1: DocumentData, doc2: DocumentData) -> Dict[str, Any]:
        """
        Compare two documents and highlight differences.
        
        Args:
            doc1: First document
            doc2: Second document
            
        Returns:
            Comparison result dictionary
        """
        differences = {}
        
        # Compare all fields
        fields_to_compare = [
            'document_type', 'nama', 'alamat', 'nik', 
            'npwp_15', 'npwp_16', 'npwp_type'
        ]
        
        for field in fields_to_compare:
            val1 = getattr(doc1, field, None)
            val2 = getattr(doc2, field, None)
            
            # Convert enums to values for comparison
            if hasattr(val1, 'value'):
                val1 = val1.value
            if hasattr(val2, 'value'):
                val2 = val2.value
            
            if val1 != val2:
                differences[field] = {
                    'doc1': val1,
                    'doc2': val2
                }
        
        return {
            'are_identical': len(differences) == 0,
            'differences': differences,
            'total_differences': len(differences)
        }
    
    def export_to_dict(self, document_data: DocumentData, 
                      include_metadata: bool = True) -> Dict[str, Any]:
        """
        Export document data to dictionary with optional metadata.
        
        Args:
            document_data: Document data to export
            include_metadata: Whether to include metadata fields
            
        Returns:
            Dictionary representation
        """
        base_dict = document_data.to_dict()
        
        if not include_metadata:
            # Remove metadata fields
            metadata_fields = [
                'confidence_score', 'extraction_timestamp', 'ai_service_used'
            ]
            for field in metadata_fields:
                base_dict.pop(field, None)
        
        # Add computed fields
        base_dict['formatted_npwp_15'] = document_data.formatted_npwp_15
        base_dict['formatted_primary_id'] = document_data.formatted_primary_id
        base_dict['display_name'] = document_data.display_name
        base_dict['summary_text'] = document_data.get_summary_text()
        
        return base_dict
    
    def create_edit_options(self, document_data: DocumentData) -> List[Dict[str, str]]:
        """
        Create edit options based on available document data.
        
        Args:
            document_data: Document data to create options for
            
        Returns:
            List of edit option dictionaries
        """
        options = []
        
        # Always available fields
        options.extend([
            {"field": "nama", "display": "👤 Nama", "current": document_data.nama},
        ])
        
        if document_data.alamat:
            options.append({
                "field": "alamat", 
                "display": "🏠 Alamat", 
                "current": document_data.alamat[:50] + "..." if len(document_data.alamat) > 50 else document_data.alamat
            })
        
        # Document-specific fields
        if document_data.document_type == DocumentType.KTP and document_data.nik:
            options.append({
                "field": "nik",
                "display": "🔢 NIK",
                "current": self.format_id_16_digit(document_data.nik)
            })
        
        elif document_data.document_type == DocumentType.NPWP:
            if document_data.npwp_15:
                options.append({
                    "field": "npwp_15",
                    "display": "🔢 NPWP 15",
                    "current": self.format_npwp_15(document_data.npwp_15)
                })
            
            if document_data.npwp_16:
                options.append({
                    "field": "npwp_16", 
                    "display": "🔢 NPWP 16",
                    "current": self.format_id_16_digit(document_data.npwp_16)
                })
        
        return options
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics (placeholder for future implementation).
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_processed": 0,  # Would be tracked in database
            "success_rate": 0.0,
            "average_processing_time": 0.0,
            "common_errors": [],
            "last_reset": datetime.now().isoformat()
        }