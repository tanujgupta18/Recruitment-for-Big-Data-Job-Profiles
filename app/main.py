from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from .models import JobIn, ResumeIn, MatchRequest
from .recommend import matcher

app = FastAPI(title="Scalable Recruiting (Medium)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}

@app.post("/jobs")
def add_job(job: JobIn):
    return matcher.add_job(job.model_dump())

@app.post("/resumes")
def add_resume(resume: ResumeIn):
    return matcher.add_resume(resume.model_dump())

@app.post("/recommend")
def recommend(req: MatchRequest):
    results = matcher.match_for_job(
        description=req.description,
        top_k=req.top_k,
        location=req.location,
        min_exp=req.min_exp,
    )
    return {"count": len(results), "results": results}
