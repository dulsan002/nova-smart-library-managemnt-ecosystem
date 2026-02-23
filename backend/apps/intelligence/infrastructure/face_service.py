"""
Nova — Face Recognition Service
====================================
Compares a selfie photo against the face in an identity document
to verify that the person submitting the document is its owner.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from django.conf import settings

logger = logging.getLogger('nova.intelligence.face')


@dataclass
class FaceMatchResult:
    is_match: bool
    distance: float          # Euclidean distance (lower = more similar)
    confidence: float        # 0.0–1.0 (higher = more confident match)
    faces_in_document: int   # Number of faces detected in the ID document
    faces_in_selfie: int     # Number of faces detected in the selfie
    error: Optional[str] = None


class FaceRecognitionService:
    """
    Wraps the ``face_recognition`` library to perform 1:1 face
    verification between a selfie and an identity document photo.
    """

    def __init__(self):
        ai_config = getattr(settings, 'AI_CONFIG', {})
        self.tolerance = ai_config.get('FACE_MATCH_THRESHOLD', 0.6)
        self.model = ai_config.get('FACE_ENCODING_MODEL', 'large')
        self.num_jitters = ai_config.get('FACE_JITTERS', 2)

    def verify(
        self,
        document_image_path: str,
        selfie_image_path: str,
    ) -> FaceMatchResult:
        """
        Compare faces from two images.

        Returns a FaceMatchResult with match status, distance, and
        confidence.
        """
        try:
            import face_recognition
            import numpy as np

            # Load images
            doc_image = face_recognition.load_image_file(document_image_path)
            selfie_image = face_recognition.load_image_file(selfie_image_path)

            # Detect and encode faces
            doc_locations = face_recognition.face_locations(
                doc_image, model='hog',
            )
            selfie_locations = face_recognition.face_locations(
                selfie_image, model='hog',
            )

            if not doc_locations:
                logger.warning('No face detected in document image.')
                return FaceMatchResult(
                    is_match=False,
                    distance=1.0,
                    confidence=0.0,
                    faces_in_document=0,
                    faces_in_selfie=len(selfie_locations),
                    error='No face detected in identity document.',
                )

            if not selfie_locations:
                logger.warning('No face detected in selfie image.')
                return FaceMatchResult(
                    is_match=False,
                    distance=1.0,
                    confidence=0.0,
                    faces_in_document=len(doc_locations),
                    faces_in_selfie=0,
                    error='No face detected in selfie.',
                )

            # Encode the first (largest) face from each image
            doc_encodings = face_recognition.face_encodings(
                doc_image,
                known_face_locations=[doc_locations[0]],
                num_jitters=self.num_jitters,
                model=self.model,
            )
            selfie_encodings = face_recognition.face_encodings(
                selfie_image,
                known_face_locations=[selfie_locations[0]],
                num_jitters=self.num_jitters,
                model=self.model,
            )

            if not doc_encodings or not selfie_encodings:
                return FaceMatchResult(
                    is_match=False,
                    distance=1.0,
                    confidence=0.0,
                    faces_in_document=len(doc_locations),
                    faces_in_selfie=len(selfie_locations),
                    error='Failed to encode one or more faces.',
                )

            # Compute Euclidean distance
            distance = float(face_recognition.face_distance(
                [doc_encodings[0]], selfie_encodings[0],
            )[0])

            # Convert distance to confidence (0–1 scale)
            # distance=0 → confidence=1, distance>=tolerance*2 → confidence≈0
            confidence = max(0.0, 1.0 - (distance / (self.tolerance * 2)))
            is_match = distance <= self.tolerance

            logger.info(
                'Face verification: match=%s, distance=%.4f, '
                'confidence=%.2f, threshold=%.2f',
                is_match, distance, confidence, self.tolerance,
            )

            return FaceMatchResult(
                is_match=is_match,
                distance=distance,
                confidence=confidence,
                faces_in_document=len(doc_locations),
                faces_in_selfie=len(selfie_locations),
            )

        except ImportError:
            logger.error(
                'face_recognition library not installed. '
                'Install with: pip install face-recognition',
            )
            return FaceMatchResult(
                is_match=False,
                distance=1.0,
                confidence=0.0,
                faces_in_document=0,
                faces_in_selfie=0,
                error='face_recognition library not available.',
            )
        except Exception as exc:
            logger.error('Face verification failed: %s', exc)
            return FaceMatchResult(
                is_match=False,
                distance=1.0,
                confidence=0.0,
                faces_in_document=0,
                faces_in_selfie=0,
                error=str(exc),
            )

    def detect_face_count(self, image_path: str) -> int:
        """Utility: count faces in an image."""
        try:
            import face_recognition
            image = face_recognition.load_image_file(image_path)
            locations = face_recognition.face_locations(image, model='hog')
            return len(locations)
        except Exception as exc:
            logger.error('Face detection failed: %s', exc)
            return 0
