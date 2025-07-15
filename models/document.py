"""
Document models for KTP and NPWP data structures.
Provides type-safe data containers with business logic methods.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class DocumentType(Enum):
    """Enum for supported document types."""
    KTP = "KTP"
    NPWP = "NPWP"


class NPWPType(Enum):
    """Enum for NPWP types."""
    PERSONAL = "personal"
    COMPANY = "company"


@dataclass
class DocumentData:
    """
    Data model for extracted document information.
    Provides business logic methods and data validation.
    """
    document_type: DocumentType
    nama: str
    alamat: Optional[str] = None
    nik: Optional[str] = None
    npwp_15: Optional[str] = None
    npwp_16: Optional[str] = None
    npwp_type: Optional[NPWPType] = None
    
    # Metadata fields
    confidence_score: Optional[float] = None
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    ai_service_used: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization validation and cleanup."""
        # Clean up numeric fields
        if self.nik:
            self.nik = self._clean_number(self.nik)
        if self.npwp_15:
            self.npwp_15 = self._clean_number(self.npwp_15)
        if self.npwp_16:
            self.npwp_16 = self._clean_number(self.npwp_16)
        
        # Clean up text fields
        if self.nama:
            self.nama = self.nama.strip()
        if self.alamat:
            self.alamat = self.alamat.strip()
    
    @staticmethod
    def _clean_number(number_str: str) -> str:
        """Remove non-digit characters from number string."""
        if not number_str:
            return ""
        return re.sub(r'\D', '', str(number_str))
    
    @property
    def id_tku(self) -> str:
        """
        Generate ID TKU for company NPWP.
        Format: NPWP16 + "000000"
        """
        if (self.document_type == DocumentType.NPWP and 
            self.npwp_type == NPWPType.COMPANY and 
            self.npwp_15):
            # Convert NPWP15 to NPWP16 by prepending 0
            npwp_16 = f"0{self.npwp_15}"
            return f"{npwp_16}000000"
        return ""
    
    @property
    def primary_id(self) -> Optional[str]:
        """Get the primary identification number based on document type."""
        if self.document_type == DocumentType.KTP:
            return self.nik
        elif self.document_type == DocumentType.NPWP:
            return self.npwp_16 or self.nik
        return None
    
    @property
    def display_name(self) -> str:
        """Get display name for the document type."""
        if self.document_type == DocumentType.NPWP and self.npwp_type:
            type_display = "Perusahaan" if self.npwp_type == NPWPType.COMPANY else "Orang Pribadi"
            return f"NPWP {type_display}"
        return self.document_type.value
    
    @property
    def formatted_npwp_15(self) -> str:
        """Format NPWP 15 with dots and dash: xx.xxx.xxx.x-xxx.xxx"""
        if not self.npwp_15 or len(self.npwp_15) != 15:
            return self.npwp_15 or ""
        
        npwp = self.npwp_15
        return f"{npwp[0:2]}.{npwp[2:5]}.{npwp[5:8]}.{npwp[8:9]}-{npwp[9:12]}.{npwp[12:15]}"
    
    @property
    def formatted_primary_id(self) -> str:
        """Format primary ID with spaces: xxxx xxxx xxxx xxxx"""
        primary_id = self.primary_id
        if not primary_id or len(primary_id) != 16:
            return primary_id or ""
        
        return f"{primary_id[0:4]} {primary_id[4:8]} {primary_id[8:12]} {primary_id[12:16]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'document_type': self.document_type.value,
            'nama': self.nama,
            'alamat': self.alamat,
            'nik': self.nik,
            'npwp_15': self.npwp_15,
            'npwp_16': self.npwp_16,
            'npwp_type': self.npwp_type.value if self.npwp_type else None,
            'id_tku': self.id_tku,
            'primary_id': self.primary_id,
            'confidence_score': self.confidence_score,
            'extraction_timestamp': self.extraction_timestamp.isoformat(),
            'ai_service_used': self.ai_service_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentData':
        """Create DocumentData from dictionary."""
        # Convert string enums back to enum objects
        doc_type = DocumentType(data['document_type'])
        npwp_type = None
        if data.get('npwp_type'):
            npwp_type = NPWPType(data['npwp_type'])
        
        # Handle timestamp
        timestamp = datetime.now()
        if data.get('extraction_timestamp'):
            try:
                timestamp = datetime.fromisoformat(data['extraction_timestamp'])
            except (ValueError, TypeError):
                pass
        
        return cls(
            document_type=doc_type,
            nama=data['nama'],
            alamat=data.get('alamat'),
            nik=data.get('nik'),
            npwp_15=data.get('npwp_15'),
            npwp_16=data.get('npwp_16'),
            npwp_type=npwp_type,
            confidence_score=data.get('confidence_score'),
            extraction_timestamp=timestamp,
            ai_service_used=data.get('ai_service_used')
        )
    
    def to_sheet_row(self, nama_toko: str = "") -> List[str]:
        """
        Convert document data to spreadsheet row format.
        Matches the expected Google Sheets structure.
        """
        # Determine additional fields for company NPWP
        jenis_id_pembeli = ""
        nomor_dokumen_pembeli = ""
        
        if (self.document_type == DocumentType.NPWP and 
            self.npwp_type == NPWPType.COMPANY):
            jenis_id_pembeli = "TIN"
            nomor_dokumen_pembeli = "-"
        
        return [
            self.document_type.value,          # Column A: Tipe Dokumen
            nama_toko,                         # Column B: Nama Toko
            "",                                # Column C: Empty column
            jenis_id_pembeli,                  # Column D: Jenis ID Pembeli
            nomor_dokumen_pembeli,             # Column E: Nomor Dokumen Pembeli
            self.npwp_15 or "",               # Column F: NPWP 15
            self.primary_id or "",            # Column G: NPWP 16 / NIK
            self.id_tku,                      # Column H: ID TKU
            self.nama,                        # Column I: Nama
            self.alamat or ""                 # Column J: Alamat
        ]
    
    def get_duplicate_check_values(self) -> List[str]:
        """
        Get values that should be checked for duplicates.
        Returns list of non-empty values to check against existing data.
        """
        check_values = []
        
        if self.npwp_15:
            check_values.append(self.npwp_15)
        
        if self.primary_id:
            check_values.append(self.primary_id)
        
        if self.id_tku:
            check_values.append(self.id_tku)
        
        return check_values
    
    def validate_completeness(self) -> List[str]:
        """
        Validate that required fields are present.
        Returns list of missing required fields.
        """
        errors = []
        
        if not self.nama or not self.nama.strip():
            errors.append("Nama tidak boleh kosong")
        
        if self.document_type == DocumentType.KTP:
            if not self.nik:
                errors.append("NIK diperlukan untuk KTP")
        
        elif self.document_type == DocumentType.NPWP:
            if not self.npwp_15:
                errors.append("NPWP 15 digit diperlukan untuk NPWP")
        
        return errors
    
    def get_summary_text(self) -> str:
        """Get a summary text for display purposes."""
        summary_parts = [
            f"📋 {self.display_name}",
            f"👤 {self.nama}"
        ]
        
        if self.document_type == DocumentType.KTP and self.nik:
            summary_parts.append(f"🔢 NIK: {self.formatted_primary_id}")
        
        elif self.document_type == DocumentType.NPWP:
            if self.npwp_15:
                summary_parts.append(f"🔢 NPWP: {self.formatted_npwp_15}")
            if self.primary_id:
                summary_parts.append(f"🔢 ID: {self.formatted_primary_id}")
        
        if self.alamat:
            # Truncate long addresses for summary
            alamat_display = self.alamat[:50] + "..." if len(self.alamat) > 50 else self.alamat
            summary_parts.append(f"🏠 {alamat_display}")
        
        return "\n".join(summary_parts)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"DocumentData({self.document_type.value}, {self.nama}, {self.primary_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"DocumentData("
            f"type={self.document_type.value}, "
            f"nama='{self.nama}', "
            f"nik='{self.nik}', "
            f"npwp_15='{self.npwp_15}', "
            f"npwp_16='{self.npwp_16}', "
            f"npwp_type={self.npwp_type.value if self.npwp_type else None}"
            f")"
        )