import io
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os

from app.core.config import settings
from app.models.invoices import OCRResult, InvoiceLineItem

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Set tesseract command if configured
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    async def process_invoice_file(self, file_path: str, file_format: str) -> OCRResult:
        """Process an invoice file and extract text/data using OCR"""
        try:
            start_time = datetime.utcnow()
            
            # Convert file to images if needed
            images = await self._convert_to_images(file_path, file_format)
            
            if not images:
                return OCRResult(
                    success=False,
                    errors=["Failed to convert file to processable format"]
                )
            
            # Process all pages/images
            all_text = []
            confidence_scores = []
            
            for image in images:
                text, confidence = await self._extract_text_from_image(image)
                all_text.append(text)
                if confidence:
                    confidence_scores.append(confidence)
            
            # Combine all text
            full_text = "\n".join(all_text)
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
            
            # Extract structured data from text
            structured_data = await self._extract_structured_data(full_text)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return OCRResult(
                success=True,
                confidence=avg_confidence,
                extracted_text=full_text,
                structured_data=structured_data,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing invoice file: {str(e)}")
            return OCRResult(
                success=False,
                errors=[f"Processing error: {str(e)}"]
            )
    
    async def _convert_to_images(self, file_path: str, file_format: str) -> List[Image.Image]:
        """Convert various file formats to PIL Images"""
        loop = asyncio.get_event_loop()
        
        try:
            if file_format.upper() == 'PDF':
                return await loop.run_in_executor(
                    self.executor, 
                    lambda: convert_from_path(file_path, dpi=300)
                )
            else:
                # Handle image files (JPEG, PNG, etc.)
                image = await loop.run_in_executor(
                    self.executor,
                    lambda: Image.open(file_path)
                )
                return [image]
        except Exception as e:
            logger.error(f"Error converting file to images: {str(e)}")
            return []
    
    async def _extract_text_from_image(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """Extract text from a single image using Tesseract OCR"""
        loop = asyncio.get_event_loop()
        
        try:
            # Preprocess image for better OCR results
            processed_image = await self._preprocess_image(image)
            
            # Extract text with confidence data
            ocr_data = await loop.run_in_executor(
                self.executor,
                lambda: pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            )
            
            # Filter out low-confidence text
            text_parts = []
            confidences = []
            
            for i, confidence in enumerate(ocr_data['conf']):
                if int(confidence) > 30:  # Minimum confidence threshold
                    text = ocr_data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(int(confidence))
            
            extracted_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else None
            
            return extracted_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return "", None
    
    async def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy"""
        loop = asyncio.get_event_loop()
        
        def process():
            # Convert PIL Image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 5)
            
            # Apply adaptive thresholding
            threshold = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL Image
            return Image.fromarray(cleaned)
        
        return await loop.run_in_executor(self.executor, process)
    
    async def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from OCR text"""
        structured_data = {
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "supplier_name": None,
            "supplier_address": None,
            "total_amount": None,
            "subtotal": None,
            "tax_amount": None,
            "line_items": [],
            "currency": None
        }
        
        try:
            # Extract invoice number
            invoice_patterns = [
                r"invoice\s*#?\s*:?\s*([A-Z0-9\-]+)",
                r"inv\s*#?\s*:?\s*([A-Z0-9\-]+)",
                r"bill\s*#?\s*:?\s*([A-Z0-9\-]+)"
            ]
            for pattern in invoice_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    structured_data["invoice_number"] = match.group(1)
                    break
            
            # Extract dates
            date_patterns = [
                r"date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"(\d{4}-\d{2}-\d{2})"
            ]
            dates_found = []
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                dates_found.extend(matches)
            
            if dates_found:
                structured_data["invoice_date"] = dates_found[0]
                if len(dates_found) > 1:
                    structured_data["due_date"] = dates_found[1]
            
            # Extract total amount
            amount_patterns = [
                r"total\s*:?\s*\$?([0-9,]+\.?\d*)",
                r"amount\s*due\s*:?\s*\$?([0-9,]+\.?\d*)",
                r"balance\s*:?\s*\$?([0-9,]+\.?\d*)"
            ]
            for pattern in amount_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        structured_data["total_amount"] = float(amount_str)
                        break
                    except ValueError:
                        continue
            
            # Extract subtotal and tax
            subtotal_match = re.search(r"subtotal\s*:?\s*\$?([0-9,]+\.?\d*)", text, re.IGNORECASE)
            if subtotal_match:
                try:
                    structured_data["subtotal"] = float(subtotal_match.group(1).replace(',', ''))
                except ValueError:
                    pass
            
            tax_patterns = [
                r"tax\s*:?\s*\$?([0-9,]+\.?\d*)",
                r"vat\s*:?\s*\$?([0-9,]+\.?\d*)"
            ]
            for pattern in tax_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        structured_data["tax_amount"] = float(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        continue
            
            # Extract supplier name (usually at the top)
            lines = text.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if len(line) > 10 and line.isupper():
                    structured_data["supplier_name"] = line
                    break
            
            # Extract currency
            currency_patterns = [r"\$", r"USD", r"EUR", r"GBP"]
            for pattern in currency_patterns:
                if re.search(pattern, text):
                    if pattern == r"\$":
                        structured_data["currency"] = "USD"
                    else:
                        structured_data["currency"] = pattern
                    break
            
            # Try to extract line items (basic pattern matching)
            line_items = await self._extract_line_items(text)
            structured_data["line_items"] = line_items
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
        
        return structured_data
    
    async def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items from invoice text"""
        line_items = []
        
        try:
            lines = text.split('\n')
            
            # Look for table-like structures
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Look for lines that contain quantity, description, and amount
                # Pattern: quantity + description + unit_price + total
                pattern = r'(\d+(?:\.\d+)?)\s+(.+?)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
                match = re.match(pattern, line)
                
                if match:
                    try:
                        quantity = float(match.group(1))
                        description = match.group(2).strip()
                        unit_price = float(match.group(3).replace(',', ''))
                        total_amount = float(match.group(4).replace(',', ''))
                        
                        line_item = {
                            "description": description,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "total_amount": total_amount,
                            "net_amount": total_amount
                        }
                        
                        line_items.append(line_item)
                    except ValueError:
                        continue
                        
        except Exception as e:
            logger.error(f"Error extracting line items: {str(e)}")
        
        return line_items
    
    async def validate_extraction(self, ocr_result: OCRResult) -> Dict[str, Any]:
        """Validate the OCR extraction results"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "confidence_score": 0.0
        }
        
        if not ocr_result.success:
            validation_result["is_valid"] = False
            validation_result["errors"].append("OCR processing failed")
            return validation_result
        
        structured_data = ocr_result.structured_data or {}
        
        # Check required fields
        required_fields = ["invoice_number", "supplier_name", "total_amount"]
        missing_fields = []
        
        for field in required_fields:
            if not structured_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            validation_result["warnings"].append(f"Missing fields: {', '.join(missing_fields)}")
        
        # Validate amounts
        if structured_data.get("subtotal") and structured_data.get("tax_amount") and structured_data.get("total_amount"):
            expected_total = structured_data["subtotal"] + structured_data["tax_amount"]
            actual_total = structured_data["total_amount"]
            
            if abs(expected_total - actual_total) > 0.01:
                validation_result["warnings"].append("Total amount doesn't match subtotal + tax")
        
        # Calculate confidence score
        confidence_factors = []
        
        if ocr_result.confidence:
            confidence_factors.append(ocr_result.confidence / 100.0)
        
        if structured_data.get("invoice_number"):
            confidence_factors.append(0.2)
        
        if structured_data.get("supplier_name"):
            confidence_factors.append(0.2)
        
        if structured_data.get("total_amount"):
            confidence_factors.append(0.3)
        
        if structured_data.get("line_items"):
            confidence_factors.append(0.2)
        
        validation_result["confidence_score"] = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        
        return validation_result

# Global OCR service instance
ocr_service = OCRService()
