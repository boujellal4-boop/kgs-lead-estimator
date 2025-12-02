from fastapi import FastAPI
from pydantic import BaseModel
import json, os

app = FastAPI()
BASE = os.path.dirname(__file__)

with open(os.path.join(BASE, "averages.json")) as f:
    A = json.load(f)

class LeadRequest(BaseModel):
    lead_type: str
    country: str = None
    industry: str = None
    technology: str = None
    job_title: str = None

# simple multipliers (explainable & tunable)
LEAD_MULTIPLIER = {
    "end user": 1.0,
    "distributor": 0.6,
    "installer": 0.5,
    "consultant": 0.4
}

JOB_MULTIPLIER_KEYWORDS = {
    "ceo": 1.3, "cfo": 1.3, "owner": 1.3, "founder": 1.25,
    "director": 1.15, "head": 1.15, "manager": 1.1,
    "engineer": 0.95, "technician": 0.9, "installer": 0.85
}

def job_multiplier(title: str):
    if not title: return 1.0
    t = title.lower()
    for k,v in JOB_MULTIPLIER_KEYWORDS.items():
        if k in t: return v
    return 1.0

@app.post("/estimate")
def estimate(req: LeadRequest):
    # fetch averages (fallback to overall_average)
    tech_avg = A.get("by_technology", {}).get((req.technology or "").strip(), A["overall_average"])
    country_avg = A.get("by_country", {}).get((req.country or "").strip(), A["overall_average"])
    region = None
    # find region by country mapping in averages if exists
    # fallback to overall
    region_avg = A.get("by_region", {}).get((req.country or "").strip(), A["overall_average"])
    industry_avg = A.get("by_industry", {}).get((req.industry or "").strip(), A["overall_average"])
    lead_avg = A.get("by_lead_type", {}).get((req.lead_type or "").strip(), A["overall_average"])

    # simple explainable formula: mean of available averages
    parts = [p for p in [tech_avg, country_avg, region_avg, industry_avg, lead_avg] if p is not None]
    base = sum(parts) / max(1, len(parts))

    lm = LEAD_MULTIPLIER.get(req.lead_type.lower(), 1.0)
    jm = job_multiplier(req.job_title)

    expected = base * lm * jm
    low = expected * 0.8
    high = expected * 1.2

    return {
        "expected": round(expected,2),
        "low": round(low,2),
        "high": round(high,2),
        "components": {
            "tech_avg": tech_avg, "country_avg": country_avg, "region_avg": region_avg,
            "industry_avg": industry_avg, "lead_avg": lead_avg, "base": round(base,2),
            "lead_multiplier": lm, "job_multiplier": jm
        }
    }
