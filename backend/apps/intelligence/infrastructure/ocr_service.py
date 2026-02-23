"""
Nova — OCR Service
======================
Extracts text from identity document images using Tesseract OCR.
Used by the identity verification pipeline.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger('nova.intelligence.ocr')


@dataclass
class OCRResult:
    raw_text: str
    extracted_name: str
    extracted_id_number: str
    confidence: float  # 0.0–1.0
    document_type: str  # 'NIC', 'PASSPORT', 'DRIVING_LICENSE', 'UNKNOWN'


class OCRService:
    """
    Wraps pytesseract to extract identity information from
    scanned documents.
    """

    # Regex patterns for Sri Lankan NIC / passport / driving licence
    NIC_OLD_PATTERN = re.compile(r'\b(\d{9}[VvXx])\b')
    NIC_NEW_PATTERN = re.compile(r'\b(\d{12})\b')
    PASSPORT_PATTERN = re.compile(r'\b([A-Z]\d{7})\b')
    DL_PATTERN = re.compile(r'\b([A-Z]\d{7,8})\b')

    def __init__(self):
        ai_config = getattr(settings, 'AI_CONFIG', {})
        self.tesseract_cmd = ai_config.get('TESSERACT_CMD', 'tesseract')
        self.lang = ai_config.get('OCR_LANGUAGE', 'eng')

    def extract(self, image_path: str) -> OCRResult:
        """
        Run OCR on the given image and extract identity fields.
        """
        try:
            import pytesseract
            from PIL import Image

            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

            img = Image.open(image_path)

            # Pre-process: convert to greyscale for better OCR accuracy
            if img.mode != 'L':
                img = img.convert('L')

            # Full OCR
            data = pytesseract.image_to_data(
                img, lang=self.lang, output_type=pytesseract.Output.DICT,
            )
            raw_text = pytesseract.image_to_string(img, lang=self.lang)

            # Compute average confidence from detected words
            confidences = [
                int(c) for c in data.get('conf', [])
                if str(c).lstrip('-').isdigit() and int(c) > 0
            ]
            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0
                if confidences else 0.0
            )

            # Extract document number
            id_number, doc_type = self._extract_document_number(raw_text)

            # Extract name (heuristic: line after "Name" label)
            name = self._extract_name(raw_text)

            logger.info(
                'OCR completed: doc_type=%s, confidence=%.2f, id=%s',
                doc_type, avg_confidence, id_number[:4] + '***' if id_number else 'N/A',
            )

            return OCRResult(
                raw_text=raw_text,
                extracted_name=name,
                extracted_id_number=id_number,
                confidence=avg_confidence,
                document_type=doc_type,
            )

        except Exception as exc:
            logger.error('OCR extraction failed: %s', exc)
            return OCRResult(
                raw_text='',
                extracted_name='',
                extracted_id_number='',
                confidence=0.0,
                document_type='UNKNOWN',
            )

    def _extract_document_number(self, text: str):
        """Try to match an ID number from the OCR text."""
        # Try new NIC (12-digit)
        match = self.NIC_NEW_PATTERN.search(text)
        if match:
            return match.group(1), 'NIC'

        # Try old NIC (9 digits + V/X)
        match = self.NIC_OLD_PATTERN.search(text)
        if match:
            return match.group(1), 'NIC'

        # Try passport
        match = self.PASSPORT_PATTERN.search(text)
        if match:
            return match.group(1), 'PASSPORT'

        # Try driving licence
        match = self.DL_PATTERN.search(text)
        if match:
            return match.group(1), 'DRIVING_LICENSE'

        return '', 'UNKNOWN'

    def _extract_name(self, text: str) -> str:
        """
        Heuristic name extraction — look for lines after common labels.
        """
        lines = text.split('\n')
        name_labels = ['name', 'full name', 'holder', 'surname']

        for i, line in enumerate(lines):
            lower = line.lower().strip()
            for label in name_labels:
                if label in lower:
                    # The name might be on the same line after a colon
                    if ':' in line:
                        candidate = line.split(':', 1)[1].strip()
                        if candidate and len(candidate) > 2:
                            return self._clean_name(candidate)
                    # Or on the next line
                    if i + 1 < len(lines):
                        candidate = lines[i + 1].strip()
                        if candidate and len(candidate) > 2:
                            return self._clean_name(candidate)
        return ''

    def extract_both_sides(self, front_path: str, back_path: Optional[str] = None) -> OCRResult:
        """
        Extract from both sides of a NIC card and merge the best results.
        The front side typically has the name and NIC number.
        The back side may contain additional details (address, DOB, etc.)
        and sometimes a secondary NIC number print.
        """
        front_result = self.extract(front_path)

        if not back_path:
            return front_result

        back_result = self.extract(back_path)

        # Merge: prefer whichever side extracted each field more reliably
        merged_name = front_result.extracted_name or back_result.extracted_name
        merged_id = front_result.extracted_id_number or back_result.extracted_id_number

        # If both sides found the same NIC number, boost confidence
        confidence_boost = 0.0
        if (
            front_result.extracted_id_number
            and back_result.extracted_id_number
            and front_result.extracted_id_number.replace(' ', '').upper()
            == back_result.extracted_id_number.replace(' ', '').upper()
        ):
            confidence_boost = 0.10  # +10% when both sides agree

        merged_confidence = min(
            1.0,
            max(front_result.confidence, back_result.confidence) + confidence_boost,
        )

        # Combine raw text from both sides
        merged_raw = (
            '--- FRONT ---\n'
            + front_result.raw_text
            + '\n--- BACK ---\n'
            + back_result.raw_text
        )

        doc_type = front_result.document_type
        if doc_type == 'UNKNOWN':
            doc_type = back_result.document_type

        logger.info(
            'OCR both sides: front_conf=%.2f, back_conf=%.2f, merged=%.2f, boost=%.2f',
            front_result.confidence, back_result.confidence,
            merged_confidence, confidence_boost,
        )

        return OCRResult(
            raw_text=merged_raw,
            extracted_name=merged_name,
            extracted_id_number=merged_id,
            confidence=merged_confidence,
            document_type=doc_type,
        )

    @staticmethod
    def _clean_name(name: str) -> str:
        """Remove non-alpha characters except spaces and dots."""
        cleaned = re.sub(r'[^a-zA-Z\s.]', '', name).strip()
        # Collapse whitespace
        return re.sub(r'\s+', ' ', cleaned)
