import glob, os, re, time
import numpy as np, faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from openai import OpenAI

MODEL_NAME = "llama3.2"
THRESHOLD = 0.38  # refusal threshold, tuned with eval.py
EMBED_MODEL = "all-MiniLM-L6-v2"

emb = SentenceTransformer(EMBED_MODEL)
llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

DOC_LABELS = {
    "uscg": "COLREGs (USCG Navigation Rules)",
    "solas": "SOLAS",
    "marpol": "MARPOL",
}


def doc_label(filename):
    low = filename.lower()
    for key, label in DOC_LABELS.items():
        if key in low:
            return label
    return filename


def jurisdiction_of(text):
    """Tag a chunk as 'inland', 'international' or 'neutral' from the USCG markers."""
    inland = re.search(r"[\u2014\u2013-]\s*INLAND\s*[\u2014\u2013-]", text, re.I)
    intl = re.search(r"[\u2014\u2013-]\s*INTERNATIONAL\s*[\u2014\u2013-]", text, re.I)
    if inland and not intl:
        return "inland"
    if intl and not inland:
        return "international"
    return "neutral"


def load_chunks(size=800, overlap=150):
    out = []
    for f in sorted(glob.glob("data/*.pdf")):
        name = os.path.basename(f)
        for p, page in enumerate(PdfReader(f).pages, 1):
            t = (page.extract_text() or "").replace("\n", " ")
            for i in range(0, len(t), size - overlap):
                c = t[i:i + size].strip()
                if len(c) > 100:
                    out.append({
                        "text": c, "src": name, "page": p,
                        "label": doc_label(name), "jur": jurisdiction_of(c),
                    })
    return out


chunks = load_chunks()
vecs = emb.encode([c["text"] for c in chunks], normalize_embeddings=True)
index = faiss.IndexFlatIP(vecs.shape[1])
index.add(np.array(vecs, dtype="float32"))


def retrieve(q, k=4, sources=None, jurisdiction="Both"):
    """Return the top-k (chunk, score) pairs, optionally filtered by document and jurisdiction."""
    filtered = bool(sources) or jurisdiction != "Both"
    n = len(chunks) if filtered else k
    qv = emb.encode([q], normalize_embeddings=True)
    scores, ids = index.search(np.array(qv, dtype="float32"), n)
    hits = []
    for i, s in zip(ids[0], scores[0]):
        c = chunks[i]
        if sources and c["label"] not in sources:
            continue
        if jurisdiction == "International" and c["jur"] == "inland":
            continue
        if jurisdiction == "Inland" and c["jur"] == "international":
            continue
        hits.append((c, float(s)))
        if len(hits) == k:
            break
    return hits


def confidence_level(score, threshold=THRESHOLD):
    if score >= 0.60:
        return "High"
    if score >= max(0.45, threshold):
        return "Medium"
    return "Low"


SYSTEM_PROMPT = (
    "You are MarineRAG, an assistant for maritime safety regulations. "
    "Answer ONLY from the provided context. Be concise and use short bullet points where helpful. "
    "Cite every claim as [file p.X]. If the context shows both INLAND and INTERNATIONAL versions of a rule, "
    "say which one you are quoting. If the context does not contain the answer, say so clearly."
)


def answer(q, k=4, threshold=THRESHOLD, sources=None, jurisdiction="Both"):
    """Full RAG answer. Returns a dict so the UI and the logger can use every field."""
    t0 = time.perf_counter()
    hits = retrieve(q, k, sources, jurisdiction)
    top = hits[0][1] if hits else 0.0
    result = {"question": q, "hits": hits, "top_score": top, "refused": False,
              "confidence": confidence_level(top, threshold), "error": None}
    if not hits or top < threshold:
        result["refused"] = True
        result["answer"] = "I couldn't find this in the loaded maritime documents."
    else:
        ctx = "\n\n".join(f"[{c['src']} p.{c['page']}] {c['text']}" for c, _ in hits)
        try:
            r = llm.chat.completions.create(
                model=MODEL_NAME, temperature=0,
                messages=[{"role": "system", "content": SYSTEM_PROMPT},
                          {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion: {q}"}],
            )
            result["answer"] = r.choices[0].message.content
        except Exception as e:  # Ollama not running, model missing, etc.
            result["error"] = str(e)
            result["answer"] = ("The language model is not reachable. Start Ollama (`ollama serve`) "
                                "and try again. The retrieved sources are still shown below.")
    result["latency"] = round(time.perf_counter() - t0, 2)
    return result
