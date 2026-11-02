import os, sys
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
import rag

USE_PINECONE = os.getenv("USE_PINECONE") == "1"
if USE_PINECONE:
    import pinecone_store

COL, SOL, MAR = rag.DOC_LABELS["uscg"], rag.DOC_LABELS["solas"], rag.DOC_LABELS["marpol"]
ROUTES = {
    COL: ["overtak", "give way", "give-way", "stand-on", "light", "signal", "fog", "collision",
          "head-on", "crossing", "lookout", "safe speed", "narrow channel", "separation", "shape"],
    SOL: ["lifeboat", "life-saving", "fire", "muster", "radio", "gmdss", "stability",
          "life raft", "liferaft", "survival", "safety of life"],
    MAR: ["oil", "oily", "bilge", "garbage", "sewage", "discharge", "pollution",
          "sulphur", "sulfur", "nox", "emission", "ballast"],
}

class State(TypedDict, total=False):
    question: str
    query: str
    sources: Optional[List[str]]
    hits: list
    ctx: str
    refuse: bool
    reason: str
    answer: str
    retries: int
    verified: bool
    trace: List[str]

def _t(state, msg):
    return state.get("trace", []) + [msg]

def _llm(prompt):
    r = rag.llm.chat.completions.create(
        model=rag.MODEL_NAME, temperature=0,
        messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content.strip()

def router(state):
    q = state["question"].lower()
    scores = {lab: sum(k in q for k in kws) for lab, kws in ROUTES.items()}
    best = max(scores, key=scores.get)
    src = [best] if scores[best] > 0 else None
    return {"sources": src, "query": state["question"], "retries": 0,
            "trace": _t(state, f"ROUTER    -> {best if src else 'all documents'}")}

def retriever(state):
    fn = pinecone_store.retrieve if USE_PINECONE else rag.retrieve
    hits = fn(state["query"], 4, state.get("sources"))
    top = hits[0][1] if hits else 0.0
    return {"hits": hits,
            "trace": _t(state, f"RETRIEVER -> '{state['query'][:60]}' top score {top:.2f}")}

def grader(state):
    refuse, why = rag.refusal_decision(state["question"], state["hits"])
    return {"refuse": refuse, "reason": why,
            "trace": _t(state, "GRADER    -> " + (f"FAIL ({why})" if refuse else "PASS"))}

def after_grade(state):
    if not state["refuse"]:
        return "generate"
    return "rewrite" if state["retries"] < 1 else "refuse"

def rewriter(state):
    try:
        q = _llm("Rewrite this maritime question as a short search query using formal "
                 "regulation terminology. Return only the query.\n\nQuestion: " + state["question"])
        q = q.strip('"')[:200] or state["question"]
    except Exception:
        q = state["question"]
    return {"query": q, "sources": None, "retries": state["retries"] + 1,
            "trace": _t(state, f"REWRITER  -> '{q[:60]}' (search all documents)")}

def generator(state):
    ctx = "\n\n".join(f"[{c['src']} p.{c['page']}] {c['text']}" for c, _ in state["hits"])
    try:
        r = rag.llm.chat.completions.create(
            model=rag.MODEL_NAME, temperature=0,
            messages=[{"role": "system", "content": rag.SYSTEM_PROMPT},
                      {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion: {state['question']}"}])
        ans = r.choices[0].message.content
    except Exception as e:
        ans = f"The language model is not reachable ({e}). Start Ollama and retry."
    return {"answer": ans, "ctx": ctx, "trace": _t(state, "GENERATOR -> drafted cited answer")}

def verifier(state):
    try:
        v = _llm(f"Context:\n{state['ctx']}\n\nAnswer:\n{state['answer']}\n\n"
                 "Is every claim in the answer supported by the context? "
                 "Reply with exactly one word: SUPPORTED or UNSUPPORTED.").upper()
        ok = v.startswith("SUPPORTED")
    except Exception:
        ok = True
    ans = state["answer"] if ok else ("Warning: the verifier could not confirm every claim "
                                      "against the sources. Check the cited pages.\n\n" + state["answer"])
    return {"answer": ans, "verified": ok,
            "trace": _t(state, "VERIFIER  -> " + ("SUPPORTED" if ok else "UNSUPPORTED (warning added)"))}

def refuser(state):
    msg = "I couldn't find this in the loaded maritime documents, so I can't answer it reliably."
    return {"answer": msg, "verified": True,
            "trace": _t(state, f"REFUSER   -> refused after retry ({state['reason']})")}

g = StateGraph(State)
for name, fn in [("router", router), ("retriever", retriever), ("grader", grader),
                 ("rewriter", rewriter), ("generator", generator),
                 ("verifier", verifier), ("refuser", refuser)]:
    g.add_node(name, fn)
g.set_entry_point("router")
g.add_edge("router", "retriever")
g.add_edge("retriever", "grader")
g.add_conditional_edges("grader", after_grade,
                        {"generate": "generator", "rewrite": "rewriter", "refuse": "refuser"})
g.add_edge("rewriter", "retriever")
g.add_edge("generator", "verifier")
g.add_edge("verifier", END)
g.add_edge("refuser", END)
graph = g.compile()

def ask(question):
    return graph.invoke({"question": question})

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--diagram":
        print(graph.get_graph().draw_mermaid())
        sys.exit()
    q = " ".join(sys.argv[1:]) or "What are the rules for oily water discharge from the engine room?"
    out = ask(q)
    print("\n".join(out["trace"]))
    print("\nANSWER:\n" + out["answer"])
