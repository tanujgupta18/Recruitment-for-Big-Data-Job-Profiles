
from __future__ import annotations
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RESUME_PATH = os.path.join(DATA_DIR, "resumes.csv")
JOB_PATH = os.path.join(DATA_DIR, "jobs.csv")

class Matcher:
    def __init__(self) -> None:
        self.resumes = pd.read_csv(RESUME_PATH)
        # Create a "text" field to vectorize (skills + summary)
        self.resumes["text"] = (self.resumes["skills"].fillna("") + " " + self.resumes["summary"].fillna("")).str.lower()
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
        self.resume_matrix = self.vectorizer.fit_transform(self.resumes["text"])

    def refresh(self) -> None:
        """Reload data and rebuild vectorizer (call after uploads)."""
        self.__init__()

    def match_for_job(self, description: str, top_k: int = 10, location: Optional[str] = None, min_exp: Optional[int] = None) -> List[Dict[str, Any]]:
        q = (description or "").lower()
        q_vec = self.vectorizer.transform([q])
        sims = cosine_similarity(q_vec, self.resume_matrix).flatten()
        scores = (sims * 100).round(2)  # percentage score

        df = self.resumes.copy()
        df["score"] = scores

        if location:
            df = df[df["location"].str.lower() == location.lower()]

        if min_exp is not None:
            df = df[df["years_experience"] >= int(min_exp)]

        df = df.sort_values("score", ascending=False).head(top_k)
        cols = ["id","name","location","years_experience","skills","summary","score"]
        return df[cols].to_dict(orient="records")

    def add_resume(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        df = self.resumes
        new_id = int(df["id"].max()) + 1 if len(df) else 1
        rec["id"] = new_id
        # Append to CSV
        pd.DataFrame([rec]).to_csv(RESUME_PATH, mode="a", header=not os.path.exists(RESUME_PATH) or os.stat(RESUME_PATH).st_size==0, index=False)
        self.refresh()
        return {"id": new_id}

    def add_job(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        jobs = pd.read_csv(JOB_PATH) if os.path.exists(JOB_PATH) else pd.DataFrame(columns=["id","title","location","min_exp","description"])
        new_id = int(jobs["id"].max()) + 1 if len(jobs) else 1
        rec["id"] = new_id
        pd.DataFrame([rec]).to_csv(JOB_PATH, mode="a", header=not os.path.exists(JOB_PATH) or os.stat(JOB_PATH).st_size==0, index=False)
        return {"id": new_id}

matcher = Matcher()
