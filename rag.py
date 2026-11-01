import glob, numpy as np, faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from openai import OpenAI

emb = SentenceTransformer("all-MiniLM-L6-v2")
llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
THRESHOLD = 0.38  # tune this using your test set

def load_chunks(size=800, overlap=150):
    chunks = []
    for f in glob.glob("data/*.pdf"):
        for p, page in enumerate(PdfReader(f).pages, 1):
            t = (page.extract_text() or "").replace("\n", " ")
            for i in range(0, len(t), size - overlap):
                c = t[i:i + size].strip()
                if len(c) > 100:
                    chunks.append({"text": c, "src": f.split("/")[-1], "page": p})
    return chunks

chunks = load_chunks()
vecs = emb.encode([c["text"] for c in chunks], normalize_embeddings=True)
index = faiss.IndexFlatIP(vecs.shape[1])
index.add(np.array(vecs, dtype="float32"))

def retrieve(q, k=4):
    qv = emb.encode([q], normalize_embeddings=True)
    scores, ids = index.search(np.array(qv, dtype="float32"), k)
    return [(chunks[i], float(s)) for i, s in zip(ids[0], scores[0])]

def answer(q):
    hits = retrieve(q)
    if hits[0][1] < THRESHOLD:
        return "I couldn't find this in the loaded maritime documents.", hits
    ctx = "\n\n".join(f"[{c['src']} p.{c['page']}] {c['text']}" for c, _ in hits)
    prompt = (f"Answer ONLY from the context. Cite sources like [file p.X]. "
              f"If the context is insufficient, say so.\n\nContext:\n{ctx}\n\nQuestion: {q}")
    r = llm.chat.completions.create(model="llama3.2",
        messages=[{"role": "user", "content": prompt}], temperature=0)
    return r.choices[0].message.content, hits
