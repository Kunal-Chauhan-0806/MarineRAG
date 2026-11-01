import csv, os
from datetime import datetime

LOG_DIR = "logs"
QUERY_LOG = os.path.join(LOG_DIR, "queries.csv")
FEEDBACK_LOG = os.path.join(LOG_DIR, "feedback.csv")


def _append(path, header, row):
    os.makedirs(LOG_DIR, exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow(row)


def log_query(result, jurisdiction, sources):
    _append(QUERY_LOG,
            ["timestamp", "question", "top_score", "confidence", "refused", "latency_s", "jurisdiction", "documents"],
            [datetime.now().isoformat(timespec="seconds"), result["question"], round(result["top_score"], 3),
             result["confidence"], int(result["refused"]), result.get("latency", ""), jurisdiction,
             "|".join(sources) if sources else "all"])


def log_feedback(question, rating):
    _append(FEEDBACK_LOG, ["timestamp", "question", "rating"],
            [datetime.now().isoformat(timespec="seconds"), question, rating])


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stats():
    q, fb = _read(QUERY_LOG), _read(FEEDBACK_LOG)
    n = len(q)
    refused = sum(int(r["refused"]) for r in q)
    answered = [r for r in q if r["refused"] == "0"]
    avg_lat = sum(float(r["latency_s"] or 0) for r in answered) / len(answered) if answered else 0
    avg_score = sum(float(r["top_score"]) for r in q) / n if n else 0
    up = sum(1 for r in fb if r["rating"] == "up")
    helpful = up / len(fb) if fb else None
    return {"queries": n, "refusal_rate": refused / n if n else 0, "avg_latency": avg_lat,
            "avg_score": avg_score, "feedback_count": len(fb), "helpful_rate": helpful, "recent": q[-10:][::-1]}
