"""
AI service for document processing using OpenAI and DeepSeek.
Provides intelligent document data extraction with retry logic and validation.
"""

import asyncio
import base64
import json
import logging
from typing import Optional, Dict, Any, Tuple, List
from openai import AsyncOpenAI
import requests

from config.settings import settings
from core.exceptions import AIProcessingError, RateLimitError, AuthenticationError
from core.validators import DocumentValidator
from models.document import DocumentData, DocumentType, NPWPType


class AIService:
    """
    Service for AI-powered document processing.
    Supports multiple AI providers with automatic fallback and retry logic.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._openai_client = None
        self._setup_clients()
    
    def _setup_clients(self):
        """Initialize AI service clients."""
        if settings.OPENAI_API_KEY:
            self._openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.get_ai_config().get('timeout', 60)
            )
            self.logger.info("OpenAI client initialized")
        else:
            self.logger.warning("OpenAI API key not found")
    
    async def extract_document_data(self, image_bytes: bytes, 
                                  max_retries: int = 3) -> Optional[DocumentData]:
        """
        Extract document data from image using AI with retry logic.
        
        Args:
            image_bytes: Image data as bytes
            max_retries: Maximum number of retry attempts
            
        Returns:
            DocumentData object or None if extraction fails
            
        Raises:
            AIProcessingError: If AI processing fails after all retries
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"AI extraction attempt {attempt + 1}/{max_retries}")
                
                # Get AI response
                if settings.ACTIVE_AI_SERVICE == "openai":
                    raw_data = await self._call_openai_api(base64_image)
                elif settings.ACTIVE_AI_SERVICE == "deepseek":
                    raw_data = await self._call_deepseek_api(base64_image)
                else:
                    raise AIProcessingError(
                        f"Unknown AI service: {settings.ACTIVE_AI_SERVICE}",
                        ai_service=settings.ACTIVE_AI_SERVICE
                    )
                
                if not raw_data:
                    raise AIProcessingError("Empty response from AI service")
                
                # Parse and validate response
                document_data = self._parse_ai_response(raw_data)
                
                # Additional validation
                validation_errors = self._validate_extracted_data(document_data)
                if validation_errors:
                    self.logger.warning(f"Validation errors: {validation_errors}")
                    # Continue with the data but log warnings
                
                # Set metadata
                document_data.ai_service_used = settings.ACTIVE_AI_SERVICE
                
                self.logger.info(f"Successfully extracted {document_data.document_type.value} data")
                return document_data
                
            except RateLimitError as e:
                self.logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # Exponential backoff
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
                    
            except AuthenticationError as e:
                self.logger.error(f"Authentication error: {e}")
                raise  # Don't retry authentication errors
                
            except Exception as e:
                self.logger.error(f"AI processing error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Brief pause before retry
                else:
                    raise AIProcessingError(
                        f"AI processing failed after {max_retries} attempts: {str(e)}",
                        ai_service=settings.ACTIVE_AI_SERVICE
                    )
        
        return None
    
    async def _call_openai_api(self, base64_image: str) -> Dict[str, Any]:
        """Call OpenAI API with structured prompt."""
        if not self._openai_client:
            raise AIProcessingError("OpenAI client not initialized")
        
        try:
            prompt = self._get_extraction_prompt()
            
            response = await self._openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        },
                    ],
                }],
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent results
            )
            
            result_json = response.choices[0].message.content
            
            if not result_json:
                raise AIProcessingError("Empty response from OpenAI")
            
            return json.loads(result_json)
            
        except json.JSONDecodeError as e:
            raise AIProcessingError(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg:
                raise RateLimitError(f"OpenAI rate limit: {e}")
            elif "authentication" in error_msg or "api key" in error_msg:
                raise AuthenticationError(f"OpenAI authentication error: {e}")
            else:
                raise AIProcessingError(f"OpenAI API error: {e}")
    
    async def _call_deepseek_api(self, base64_image: str) -> Dict[str, Any]:
        """Call DeepSeek API with error handling."""
        try:
            prompt = self._get_extraction_prompt()
            
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
            }
            
            payload = {
                "model": settings.DEEPSEEK_MODEL,
                "messages": [{
                    "role": "user",
                    "content": f"data:image/jpeg;base64,{base64_image}\n{prompt}"
                }],
                "max_tokens": 1000,
                "temperature": 0.1,
            }
            
            # Use asyncio.to_thread for non-blocking requests
            response = await asyncio.to_thread(
                requests.post, 
                url, 
                headers=headers, 
                json=payload,
                timeout=settings.get_ai_config().get('timeout', 60)
            )
            
            if response.status_code == 429:
                raise RateLimitError(f"DeepSeek rate limit exceeded")
            elif response.status_code == 401:
                raise AuthenticationError(f"DeepSeek authentication failed")
            
            response.raise_for_status()
            
            result = response.json()
            result_content = result['choices'][0]['message']['content']
            
            if not result_content.strip().startswith("{"):
                raise AIProcessingError(f"Invalid response format from DeepSeek: {result_content[:100]}...")
            
            return json.loads(result_content)
            
        except requests.exceptions.Timeout:
            raise AIProcessingError("DeepSeek API timeout")
        except requests.exceptions.RequestException as e:
            raise AIProcessingError(f"DeepSeek API request error: {e}")
        except json.JSONDecodeError as e:
            raise AIProcessingError(f"Invalid JSON response from DeepSeek: {e}")
    
    def _get_extraction_prompt(self) -> str:
        """Get the structured extraction prompt for AI."""
        return """
Sebagai ahli data entry untuk dokumen resmi Indonesia, ekstrak informasi dari gambar KTP atau NPWP.
Kembalikan hasilnya HANYA dalam format JSON yang valid, tanpa penjelasan tambahan.

PENTING: Pastikan semua nomor hanya berisi DIGIT (0-9), tanpa titik, strip, atau spasi.

Ekstrak data berikut:
- "document_type": Identifikasi sebagai "KTP" atau "NPWP" (WAJIB)
- "nama": Nama lengkap sesuai dokumen (WAJIB)
- "nik": NIK 16 digit dari KTP. Jika dokumen ini NPWP, berikan null
- "npwp_15": NPWP 15 digit tanpa format. Jika dokumen ini KTP, berikan null
- "npwp_16": NPWP 16 digit tanpa format. Jika dokumen ini KTP, berikan null
- "alamat": Alamat lengkap dan terstruktur

Aturan NPWP:
- NPWP biasanya dalam format: xx.xxx.xxx.x-xxx.xxx (15 digit)
- Ekstrak HANYA angka, buang semua titik dan strip
- Contoh: "86.655.529.5-602.000" → npwp_15: "866555295602000"
- Jika ada NPWP 16 digit, masukkan ke npwp_16
- Jika NPWP dimulai dengan 0, tetap sertakan 0 tersebut

Aturan alamat:
- Untuk KTP: Sertakan RT, RW, Kelurahan/Desa, Kecamatan, Kabupaten/Kota, Provinsi
- Untuk NPWP: Alamat sesuai yang tertera di dokumen
- Gabungkan dengan pemisah koma untuk struktur yang jelas

Aturan nomor:
- Semua nomor HANYA boleh berisi digit 0-9
- Hapus semua titik (.), strip (-), dan spasi ( )
- NIK harus tepat 16 digit
- NPWP_15 harus tepat 15 digit
- NPWP_16 harus tepat 16 digit

Validasi:
- document_type harus "KTP" atau "NPWP"
- nama tidak boleh kosong
- Untuk KTP: nik wajib ada dan 16 digit
- Untuk NPWP: npwp_15 wajib ada dan 15 digit

Jika ada field yang tidak dapat dibaca atau tidak ada, berikan null.
Pastikan JSON benar-benar valid dan dapat di-parse.

Format response:
{
    "document_type": "KTP" atau "NPWP",
    "nama": "string",
    "nik": "string 16 digit atau null",
    "npwp_15": "string 15 digit atau null", 
    "npwp_16": "string 16 digit atau null",
    "alamat": "string atau null"
}
"""
    
    def _parse_ai_response(self, raw_data: Dict[str, Any]) -> DocumentData:
        """
        Parse AI response into DocumentData object.
        
        Args:
            raw_data: Raw response from AI service
            
        Returns:
            DocumentData object
            
        Raises:
            AIProcessingError: If response format is invalid
        """
        try:
            # Validate required fields
            if 'document_type' not in raw_data:
                raise AIProcessingError("Missing document_type in AI response")
            
            if 'nama' not in raw_data:
                raise AIProcessingError("Missing nama in AI response")
            
            # Parse document type
            doc_type_str = raw_data.get('document_type', '').upper().strip()
            if doc_type_str not in ['KTP', 'NPWP']:
                raise AIProcessingError(f"Invalid document type: {doc_type_str}")
            
            doc_type = DocumentType(doc_type_str)
            
            # Clean and validate numeric fields
            nik = self._clean_and_validate_number(raw_data.get('nik'), 16) if doc_type == DocumentType.KTP else None
            npwp_15 = self._clean_and_validate_number(raw_data.get('npwp_15'), 15) if doc_type == DocumentType.NPWP else None
            npwp_16 = self._clean_and_validate_number(raw_data.get('npwp_16'), 16) if doc_type == DocumentType.NPWP else None
            
            # Clean text fields
            nama = raw_data.get('nama', '').strip()
            alamat = raw_data.get('alamat', '').strip() if raw_data.get('alamat') else None
            
            if not nama:
                raise AIProcessingError("Empty nama in AI response")
            
            # Create DocumentData object
            document_data = DocumentData(
                document_type=doc_type,
                nama=nama,
                alamat=alamat,
                nik=nik,
                npwp_15=npwp_15,
                npwp_16=npwp_16
            )
            
            return document_data
            
        except Exception as e:
            if isinstance(e, AIProcessingError):
                raise
            raise AIProcessingError(f"Error parsing AI response: {e}")
    
    def _clean_and_validate_number(self, number_str: Any, expected_length: int) -> Optional[str]:
        """
        Clean and validate numeric strings.
        
        Args:
            number_str: Input number string
            expected_length: Expected length after cleaning
            
        Returns:
            Cleaned number string or None if invalid
        """
        if not number_str:
            return None
        
        # Convert to string and remove non-digits
        cleaned = ''.join(filter(str.isdigit, str(number_str)))
        
        if not cleaned:
            return None
        
        # Check length - be more flexible for NPWP
        if expected_length == 15:  # NPWP 15
            # Accept 15 digits exactly
            if len(cleaned) == 15:
                return cleaned
            # If it's 16 digits starting with 0, remove the first 0
            elif len(cleaned) == 16 and cleaned.startswith('0'):
                return cleaned[1:]
            else:
                self.logger.warning(f"NPWP length mismatch: expected 15, got {len(cleaned)}")
                return None
        elif expected_length == 16:  # NIK or NPWP 16
            if len(cleaned) == 16:
                return cleaned
            # If it's 15 digits, add leading 0 for NPWP
            elif len(cleaned) == 15:
                return '0' + cleaned
            else:
                self.logger.warning(f"Number length mismatch: expected 16, got {len(cleaned)}")
                return None
        else:
            # Other lengths - strict checking
            if len(cleaned) != expected_length:
                self.logger.warning(f"Number length mismatch: expected {expected_length}, got {len(cleaned)}")
                return None
            return cleaned
    
    def _validate_extracted_data(self, document_data: DocumentData) -> List[str]:
        """
        Validate extracted document data.
        
        Args:
            document_data: Extracted document data
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            # Convert DocumentData to dict for validation
            data_dict = {
                'document_type': document_data.document_type.value,
                'nama': document_data.nama,
                'alamat': document_data.alamat,
                'nik': document_data.nik,
                'npwp_15': document_data.npwp_15,
                'npwp_16': document_data.npwp_16
            }
            
            # Use existing validator
            validation_errors = DocumentValidator.validate_document_data(
                data_dict,
                document_data.document_type.value
            )
            errors.extend(validation_errors)
            
            # Additional AI-specific validations
            if document_data.document_type == DocumentType.KTP and not document_data.nik:
                errors.append("NIK missing for KTP document")
            
            if document_data.document_type == DocumentType.NPWP and not document_data.npwp_15:
                errors.append("NPWP 15 missing for NPWP document")
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            errors.append(f"Validation error: {e}")
        
        return errors
    
    async def get_service_health(self) -> Dict[str, Any]:
        """
        Check health of AI services.
        
        Returns:
            Dictionary with health status of each service
        """
        health_status = {
            'active_service': settings.ACTIVE_AI_SERVICE,
            'services': {}
        }
        
        # Check OpenAI
        if settings.OPENAI_API_KEY:
            try:
                if self._openai_client:
                    # Simple test call (you might want to use a smaller model for health checks)
                    test_response = await self._openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=1
                    )
                    health_status['services']['openai'] = {
                        'status': 'healthy',
                        'model': settings.OPENAI_MODEL
                    }
                else:
                    health_status['services']['openai'] = {
                        'status': 'not_initialized',
                        'model': settings.OPENAI_MODEL
                    }
            except Exception as e:
                health_status['services']['openai'] = {
                    'status': 'error',
                    'error': str(e),
                    'model': settings.OPENAI_MODEL
                }
        
        # Check DeepSeek
        if settings.DEEPSEEK_API_KEY:
            try:
                # Simple health check for DeepSeek
                health_status['services']['deepseek'] = {
                    'status': 'configured',  # We don't do actual test call to save quota
                    'model': settings.DEEPSEEK_MODEL
                }
            except Exception as e:
                health_status['services']['deepseek'] = {
                    'status': 'error',
                    'error': str(e),
                    'model': settings.DEEPSEEK_MODEL
                }
        
        return health_status
    
    def get_supported_features(self) -> Dict[str, Any]:
        """Get list of supported features and capabilities."""
        return {
            'document_types': [dt.value for dt in DocumentType],
            'npwp_types': [nt.value for nt in NPWPType],
            'ai_services': ['openai', 'deepseek'],
            'active_service': settings.ACTIVE_AI_SERVICE,
            'max_retries': 3,
            'supports_batch_processing': False,  # Future feature
            'confidence_scoring': False,  # Future feature
            'validation': True
        }