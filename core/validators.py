"""
Data validation utilities for document processing.
Provides comprehensive validation for KTP/NPWP data with detailed error messages.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .exceptions import ValidationError
from config.constants import VALIDATION_PATTERNS


class DocumentValidator:
    """
    Comprehensive validator for KTP and NPWP documents.
    Provides detailed validation with user-friendly error messages.
    """
    
    @staticmethod
    def validate_nik(nik: str) -> Tuple[bool, Optional[str]]:
        """
        Validate NIK (Nomor Induk Kependudukan) format and basic rules.
        
        Args:
            nik: NIK string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not nik:
            return False, "NIK tidak boleh kosong"
        
        # Remove spaces and non-digits
        clean_nik = re.sub(r'\D', '', str(nik))
        
        # Length check
        if len(clean_nik) != 16:
            return False, f"NIK harus 16 digit, ditemukan {len(clean_nik)} digit"
        
        # Pattern validation
        if not re.match(VALIDATION_PATTERNS["nik"], clean_nik):
            return False, "NIK harus berisi 16 digit angka"
        
        # Basic validity checks
        if clean_nik == "0" * 16:
            return False, "NIK tidak valid (semua angka nol)"
        
        if clean_nik == "1" * 16:
            return False, "NIK tidak valid (semua angka sama)"
        
        # Validate province code (first 2 digits)
        province_code = clean_nik[:2]
        if not DocumentValidator._is_valid_province_code(province_code):
            return False, f"Kode provinsi tidak valid: {province_code}"
        
        # Validate date part (digits 7-12: DDMMYY)
        date_part = clean_nik[6:12]
        if not DocumentValidator._is_valid_nik_date(date_part):
            return False, "Format tanggal lahir dalam NIK tidak valid"
        
        return True, None
    
    @staticmethod
    def validate_npwp_15(npwp: str) -> Tuple[bool, Optional[str]]:
        """
        Validate NPWP 15 digit format.
        
        Args:
            npwp: NPWP string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not npwp:
            return False, "NPWP tidak boleh kosong"
        
        # Remove formatting characters
        clean_npwp = re.sub(r'[.\-\s]', '', str(npwp))
        
        # Length check
        if len(clean_npwp) != 15:
            return False, f"NPWP harus 15 digit, ditemukan {len(clean_npwp)} digit"
        
        # Pattern validation
        if not re.match(VALIDATION_PATTERNS["npwp_15"], clean_npwp):
            return False, "NPWP harus berisi 15 digit angka"
        
        # Basic validity checks
        if clean_npwp == "0" * 15:
            return False, "NPWP tidak valid (semua angka nol)"
        
        # Remove the strict check digit validation - it's too restrictive
        # Real NPWP validation is complex and we don't need it for this use case
        
        return True, None
    
    @staticmethod
    def validate_npwp_16(npwp: str) -> Tuple[bool, Optional[str]]:
        """
        Validate NPWP 16 digit format.
        
        Args:
            npwp: NPWP string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not npwp:
            return False, "NPWP tidak boleh kosong"
        
        # Remove formatting characters
        clean_npwp = re.sub(r'[.\-\s]', '', str(npwp))
        
        # Length check
        if len(clean_npwp) != 16:
            return False, f"NPWP harus 16 digit, ditemukan {len(clean_npwp)} digit"
        
        # Pattern validation
        if not re.match(VALIDATION_PATTERNS["npwp_16"], clean_npwp):
            return False, "NPWP harus berisi 16 digit angka"
        
        # Basic validity checks
        if clean_npwp == "0" * 16:
            return False, "NPWP tidak valid (semua angka nol)"
        
        return True, None
    
    @staticmethod
    def validate_nama(nama: str) -> Tuple[bool, Optional[str]]:
        """
        Validate nama (name) format and content.
        
        Args:
            nama: Name string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not nama or not nama.strip():
            return False, "Nama tidak boleh kosong"
        
        nama = nama.strip()
        
        # Length check
        if len(nama) < 2:
            return False, "Nama terlalu pendek (minimum 2 karakter)"
        
        if len(nama) > 100:
            return False, "Nama terlalu panjang (maksimum 100 karakter)"
        
        # Content validation
        if re.match(r'^[0-9\W]+$', nama):
            return False, "Nama tidak valid (hanya berisi angka atau simbol)"
        
        # Check for suspicious patterns
        if nama.lower() in ['test', 'testing', 'admin', 'user', 'null', 'undefined']:
            return False, f"Nama '{nama}' tidak diperbolehkan"
        
        # Check for repeated characters
        if len(set(nama.replace(' ', '').lower())) < 2:
            return False, "Nama tidak valid (karakter berulang)"
        
        return True, None
    
    @staticmethod
    def validate_alamat(alamat: str) -> Tuple[bool, Optional[str]]:
        """
        Validate alamat (address) format and content.
        
        Args:
            alamat: Address string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not alamat or not alamat.strip():
            return False, "Alamat tidak boleh kosong"
        
        alamat = alamat.strip()
        
        # Length check
        if len(alamat) < 10:
            return False, "Alamat terlalu pendek (minimum 10 karakter)"
        
        if len(alamat) > 500:
            return False, "Alamat terlalu panjang (maksimum 500 karakter)"
        
        # Check for minimal address components
        required_components = ['rt', 'rw', 'kel', 'kec', 'kab', 'kot', 'prov']
        alamat_lower = alamat.lower()
        
        component_count = sum(1 for comp in required_components if comp in alamat_lower)
        
        if component_count < 2:
            return False, "Alamat harus mencakup minimal RT/RW, Kelurahan, dan Kecamatan"
        
        return True, None
    
    @classmethod
    def validate_document_data(cls, data: Dict[str, Any], document_type: str) -> List[str]:
        """
        Validate complete document data based on document type.
        
        Args:
            data: Dictionary containing document data
            document_type: Type of document ('KTP' or 'NPWP')
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate document type
        if document_type not in ['KTP', 'NPWP']:
            errors.append("Tipe dokumen harus KTP atau NPWP")
            return errors  # Stop validation if document type is invalid
        
        # Validate nama (required for all documents)
        nama = data.get('nama')
        is_valid, error = cls.validate_nama(nama)
        if not is_valid:
            errors.append(f"Nama: {error}")
        
        # Validate alamat (required for all documents)
        alamat = data.get('alamat')
        if alamat:  # Only validate if provided
            is_valid, error = cls.validate_alamat(alamat)
            if not is_valid:
                errors.append(f"Alamat: {error}")
        
        # Document-specific validation
        if document_type == 'KTP':
            # Validate NIK for KTP
            nik = data.get('nik')
            is_valid, error = cls.validate_nik(nik)
            if not is_valid:
                errors.append(f"NIK: {error}")
                
        elif document_type == 'NPWP':
            # Validate NPWP 15 (required)
            npwp_15 = data.get('npwp_15')
            is_valid, error = cls.validate_npwp_15(npwp_15)
            if not is_valid:
                errors.append(f"NPWP 15: {error}")
            
            # Validate NPWP 16 (optional)
            npwp_16 = data.get('npwp_16')
            if npwp_16:
                is_valid, error = cls.validate_npwp_16(npwp_16)
                if not is_valid:
                    errors.append(f"NPWP 16: {error}")
        
        return errors
    
    @staticmethod
    def _is_valid_province_code(code: str) -> bool:
        """
        Check if province code is valid based on Indonesia's province codes.
        """
        # Valid province codes (simplified - you can expand this)
        valid_codes = [
            '11', '12', '13', '14', '15', '16', '17', '18', '19',  # Sumatera
            '21', '22', '23', '24', '25', '26',  # Sumatera continued
            '31', '32', '33', '34', '35', '36',  # Jawa
            '51', '52', '53',  # Bali, NTB, NTT
            '61', '62', '63', '64', '65',  # Kalimantan
            '71', '72', '73', '74', '75', '76',  # Sulawesi
            '81', '82',  # Maluku
            '91', '92', '93', '94'  # Papua
        ]
        return code in valid_codes
    
    @staticmethod
    def _is_valid_nik_date(date_str: str) -> bool:
        """
        Validate date part in NIK (DDMMYY format).
        """
        if len(date_str) != 6:
            return False
        
        try:
            day = int(date_str[:2])
            month = int(date_str[2:4])
            year = int(date_str[4:6])
            
            # For women, day is added by 40
            if day > 40:
                day -= 40
            
            # Basic date validation
            if not (1 <= day <= 31):
                return False
            if not (1 <= month <= 12):
                return False
            
            # Year validation (assume 1900-2099 range)
            if year > 50:  # Assume 1950-1999
                full_year = 1900 + year
            else:  # Assume 2000-2049
                full_year = 2000 + year
            
            # Check if it's a reasonable birth year
            current_year = datetime.now().year
            if full_year > current_year or full_year < 1900:
                return False
            
            return True
            
        except ValueError:
            return False


class FileValidator:
    """
    Validator for uploaded files.
    """
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"File terlalu besar ({file_size / 1024 / 1024:.1f}MB). Maksimum {max_size_mb}MB."
        
        return True, None
    
    @staticmethod
    def validate_file_type(file_type: str, allowed_types: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate file type.
        
        Args:
            file_type: MIME type of the file
            allowed_types: List of allowed MIME types
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_type not in allowed_types:
            return False, f"Tipe file tidak didukung: {file_type}"
        
        return True, None