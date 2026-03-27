"""
Pyannote Voice Verification Service
------------------------------------
Uses pyannote.audio for speaker embedding extraction and cosine-similarity
verification.  Replaces the retiring Azure Speaker Recognition API.

Requirements:
    pip install pyannote.audio torch torchaudio
    Environment variable: HF_TOKEN  (HuggingFace User Access Token)
"""

import os
import json
import logging
import asyncio
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from pyannote.audio import Model, Inference
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logger.warning(
        "pyannote.audio not installed. Voice verification will use mock mode. "
        "Install with: pip install pyannote.audio torch torchaudio"
    )


class PyannoteService:
    """Speaker embedding extraction and voice verification using pyannote.audio."""

    # Cosine-similarity threshold — scores above this count as "same speaker"
    SIMILARITY_THRESHOLD = 0.70

    def __init__(self):
        self._model = None
        self._inference = None
        self._hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        self._initialized = False

        if not PYANNOTE_AVAILABLE:
            logger.warning("PyannoteService: pyannote.audio library not available.")
            return

        if not self._hf_token:
            logger.warning(
                "PyannoteService: HF_TOKEN not set. "
                "You must accept the model terms on HuggingFace and provide a token."
            )
            return

        try:
            # Load pre-trained speaker embedding model
            self._model = Model.from_pretrained(
                "pyannote/embedding",
                use_auth_token=self._hf_token,
            )
            self._inference = Inference(self._model, window="whole")
            self._initialized = True
            logger.info("PyannoteService initialized successfully with pyannote/embedding model.")
        except Exception as e:
            logger.error(f"PyannoteService: Failed to load model: {e}")
            self._initialized = False

    @property
    def is_available(self) -> bool:
        return self._initialized

    async def extract_voiceprint(self, audio_file_path: str) -> Optional[List[float]]:
        """
        Extract a speaker embedding (voiceprint) from an audio file.

        Args:
            audio_file_path: Path to WAV/MP3/OGG audio file on disk.

        Returns:
            List of floats representing the speaker embedding, or None on failure.
        """
        if not self._initialized:
            logger.debug("[MOCK] Returning mock voiceprint for %s", audio_file_path)
            return self._mock_voiceprint()

        try:
            # Run inference in a thread to avoid blocking the event loop
            embedding = await asyncio.to_thread(self._extract_sync, audio_file_path)
            if embedding is not None:
                # Convert numpy array to plain list for JSON serialisation
                voiceprint = embedding.tolist()
                logger.info(
                    "Voiceprint extracted (%d dims) from %s",
                    len(voiceprint),
                    Path(audio_file_path).name,
                )
                return voiceprint
            return None
        except Exception as e:
            logger.error("Error extracting voiceprint from %s: %s", audio_file_path, e)
            return None

    def _extract_sync(self, audio_file_path: str) -> Optional[np.ndarray]:
        """Synchronous embedding extraction (called inside a thread)."""
        try:
            embedding = self._inference(audio_file_path)
            # pyannote returns a 1-D numpy array
            if hasattr(embedding, "data"):
                return np.array(embedding.data).flatten()
            return np.array(embedding).flatten()
        except Exception as e:
            logger.error("_extract_sync error: %s", e)
            return None

    async def verify_voiceprint(
        self,
        audio_file_path: str,
        enrolled_embedding: List[float],
    ) -> Tuple[bool, float]:
        """
        Compare a new audio sample against an enrolled voiceprint.

        Args:
            audio_file_path: Path to the audio file to verify.
            enrolled_embedding: The stored voiceprint from enrollment.

        Returns:
            (is_same_speaker, similarity_score)
        """
        if not self._initialized:
            logger.debug("[MOCK] Returning mock verification result")
            return True, 1.0

        new_embedding = await self.extract_voiceprint(audio_file_path)
        if new_embedding is None:
            logger.warning("Could not extract embedding for verification.")
            return False, 0.0

        similarity = self._cosine_similarity(new_embedding, enrolled_embedding)
        is_same = similarity >= self.SIMILARITY_THRESHOLD

        logger.info(
            "Voice verification: similarity=%.4f threshold=%.2f result=%s",
            similarity,
            self.SIMILARITY_THRESHOLD,
            "PASS" if is_same else "FAIL",
        )
        return is_same, round(float(similarity), 4)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a_arr = np.array(a, dtype=np.float64)
        b_arr = np.array(b, dtype=np.float64)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    def _mock_voiceprint() -> List[float]:
        """Return a deterministic mock voiceprint for development."""
        rng = np.random.default_rng(seed=42)
        return rng.standard_normal(512).tolist()


# Module-level singleton
pyannote_service = PyannoteService()
