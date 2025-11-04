from __future__ import annotations
import os
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ===============================
# PATH CONFIGURATION
# ===============================
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RESUME_PATH = os.path.join(DATA_DIR, "resumes.csv")
JOB_PATH = os.path.join(DATA_DIR, "jobs.csv")


# ===============================
# MATCHER CLASS
# ===============================
class Matcher:
    def __init__(self) -> None:
        # Load resumes if file exists
        if os.path.exists(RESUME_PATH):
            self.resumes = pd.read_csv(RESUME_PATH)
        else:
            self.resumes = pd.DataFrame(
                columns=["id", "name", "email", "location", "years_experience", "skills", "summary"]
            )

        # Ensure email column exists even if old CSVs miss it
        if "email" not in self.resumes.columns:
            self.resumes["email"] = ""

        # Create a combined text field for vectorization
        if not self.resumes.empty:
            self.resumes["text"] = (
                self.resumes["skills"].fillna("") + " " + self.resumes["summary"].fillna("")
            ).str.lower()
        else:
            self.resumes["text"] = []

        # Initialize vectorizer and matrix
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        if not self.resumes.empty:
            self.resume_matrix = self.vectorizer.fit_transform(self.resumes["text"])
        else:
            self.resume_matrix = None

    # ===============================
    # REFRESH DATA
    # ===============================
    def refresh(self) -> None:
        """Reload data and rebuild vectorizer."""
        self.__init__()

    # ===============================
    # JOB MATCHING FUNCTION
    # ===============================
    def match_for_job(
        self,
        description: str,
        top_k: int = 10,
        location: Optional[str] = None,
        min_exp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if self.resumes.empty or self.resume_matrix is None:
            return []

        q = (description or "").lower()
        q_vec = self.vectorizer.transform([q])
        sims = cosine_similarity(q_vec, self.resume_matrix).flatten()
        scores = (sims * 100).round(2)

        df = self.resumes.copy()
        df["score"] = scores

        if location:
            df = df[df["location"].fillna("").str.lower() == location.lower()]

        if min_exp is not None:
            try:
                min_exp = int(min_exp)
                df["years_experience"] = pd.to_numeric(df["years_experience"], errors="coerce")
                df = df[df["years_experience"] >= min_exp]
            except ValueError:
                pass

        df = df.sort_values("score", ascending=False).head(top_k)

        # include email in results
        cols = ["id", "name", "email", "location", "years_experience", "skills", "summary", "score"]
        # some older CSVs may miss email → fill with ""
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        return df[cols].to_dict(orient="records")

    def add_resume(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        df = self.resumes
        # robust id generation even if 'id' column is empty/NaN
        new_id = int(pd.to_numeric(df.get("id", pd.Series([], dtype="float")), errors="coerce").max() or 0) + 1
        rec["id"] = new_id

        # Ensure column order for consistent CSV structure
        cols = ["id", "name", "email", "location", "years_experience", "skills", "summary"]
        row = {c: rec.get(c, "") for c in cols}
        pd.DataFrame([row]).to_csv(
            RESUME_PATH,
            mode="a",
            header=not os.path.exists(RESUME_PATH) or os.stat(RESUME_PATH).st_size == 0,
            index=False,
        )

        self.refresh()
        return {"id": new_id}
    
    # ===============================
    # ADD NEW JOB
    # ===============================
    def add_job(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        # Load existing jobs
        jobs = (
            pd.read_csv(JOB_PATH)
            if os.path.exists(JOB_PATH)
            else pd.DataFrame(columns=["id", "title", "location", "min_exp", "description"])
        )

        new_id = int(jobs["id"].max()) + 1 if len(jobs) else 1
        rec["id"] = new_id

        # ✅ Ensure fixed column order
        cols = ["id", "title", "location", "min_exp", "description"]
        row = {c: rec.get(c, "") for c in cols}

        # Save in correct format
        pd.DataFrame([row]).to_csv(
            JOB_PATH,
            mode="a",
            header=not os.path.exists(JOB_PATH) or os.stat(JOB_PATH).st_size == 0,
            index=False,
        )

        return {"id": new_id}


# ===============================
# GLOBAL INSTANCE
# ===============================
matcher = Matcher()
