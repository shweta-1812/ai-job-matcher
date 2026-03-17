from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import List


class SemanticScorer:
    """
    Role-agnostic semantic similarity scorer using sentence-transformers.
    Supports batch processing for better performance.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def score(self, resume_text: str, jd_text: str) -> float:
        """
        Cosine similarity mapped to 0..100.
        """
        if not resume_text or not jd_text:
            return 0.0

        embeddings = self.model.encode(
            [resume_text, jd_text],
            convert_to_tensor=True,
            normalize_embeddings=True
        )
        sim = util.cos_sim(embeddings[0], embeddings[1]).item()
        sim = max(0.0, float(sim))  # clamp
        return round(sim * 100.0, 2)
    
    def batch_score(self, resume_text: str, jd_texts: List[str]) -> np.ndarray:
        """
        Batch scoring for multiple job descriptions.
        Much faster than calling score() in a loop.
        
        Returns:
            Array of scores (0-100) for each JD.
        """
        if not resume_text or not jd_texts:
            return np.array([])
        
        # Encode all texts in one batch (much faster)
        all_texts = [resume_text] + jd_texts
        embeddings = self.model.encode(
            all_texts,
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        # Resume embedding is first, JD embeddings are rest
        resume_emb = embeddings[0:1]
        jd_embs = embeddings[1:]
        
        # Compute all similarities at once
        similarities = util.cos_sim(resume_emb, jd_embs).cpu().numpy().flatten()
        
        # Clamp and scale to 0-100
        similarities = np.clip(similarities, 0.0, 1.0) * 100.0
        
        return similarities
