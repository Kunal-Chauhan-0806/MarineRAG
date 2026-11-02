import collections
import streamlit as st
from rag import answer, chunks, THRESHOLD, DOC_LABELS
import analytics

st.set_page_config(page_title="MarineRAG", page_icon="⚓", layout="wide")

EXAMPLES = [
    "What are the rules for a vessel overtaking another vessel?",
    "What lights does a sailing vessel show?",
    "What does MARPOL regulate?",
    "What does SOLAS say about fire protection?",
]
BADGE = {"High": "🟢 High", "Medium": "🟡 Medium", "Low": "🔴 Low"}

# ---------------- sidebar ----------------
with st.sidebar:
    st.header("⚓ MarineRAG")
    st.caption("Maritime regulations assistant with page-cited answers.")
    st.subheader("Knowledge base")
    counts = collections.Counter(c["label"] for c in chunks)
    for label, n in counts.items():
        st.write(f"**{label}**: {n} chunks")
    st.caption(f"Total: {len(chunks)} chunks")

    st.subheader("Settings")
    k = st.slider("Passages to retrieve (top-k)", 1, 8, 4)
    threshold = st.slider("Refusal threshold", 0.20, 0.60, float(THRESHOLD), 0.01,
                          help="If the best passage scores below this, the assistant refuses to answer.")
    sources = st.multiselect("Search only in", list(counts.keys()), default=[],
                             help="Leave empty to search all documents.")
    jurisdiction = st.radio("COLREGs version", ["Both", "International", "Inland"],
                            help="The USCG manual prints International and Inland rules side by side.")
    guard = st.checkbox("Keyword grounding check", value=True,
                        help="Refuse when a named term in the question (e.g. STCW) does not appear in the retrieved passages.")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Educational prototype. Not a substitute for the official consolidated texts.")

# ---------------- state ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []


def rate(idx, rating):
    msg = st.session_state.messages[idx]
    msg["rated"] = rating
    analytics.log_feedback(msg["result"]["question"], rating)


def run_query(q):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.spinner("Searching regulations..."):
        res = answer(q, k=k, threshold=threshold, sources=sources or None, jurisdiction=jurisdiction, guard=guard)
    analytics.log_query(res, jurisdiction, sources)
    st.session_state.messages.append({"role": "assistant", "content": res["answer"], "result": res})


tab_chat, tab_stats = st.tabs(["💬 Assistant", "📊 Analytics"])

# ---------------- chat tab ----------------
with tab_chat:
    st.title("⚓ MarineRAG: Maritime Regulations Assistant")
    st.caption("Answers come only from the loaded COLREGs, SOLAS and MARPOL documents, with page citations.")

    if not st.session_state.messages:
        st.write("**Try an example:**")
        cols = st.columns(len(EXAMPLES))
        for col, ex in zip(cols, EXAMPLES):
            if col.button(ex):
                run_query(ex)
                st.rerun()

    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                r = m["result"]
                st.caption(f"Confidence: {BADGE[r['confidence']]}  |  Top score: {r['top_score']:.2f}  |  "
                           f"Response time: {r['latency']} s" + (f"  |  Refused ({r['reason']})" if r["refused"] else ""))
                if r["hits"]:
                    with st.expander(f"Sources retrieved ({len(r['hits'])})"):
                        for c, s in r["hits"]:
                            tag = f" · {c['jur']}" if c["jur"] != "neutral" else ""
                            st.markdown(f"**{c['label']}**, {c['src']} p.{c['page']}{tag} (score {s:.2f})")
                            st.caption(c["text"][:400])
                if not r["refused"]:
                    if m.get("rated"):
                        st.caption("Thanks for the feedback.")
                    else:
                        b1, b2, _ = st.columns([1, 1, 8])
                        b1.button("👍", key=f"up{i}", on_click=rate, args=(i, "up"))
                        b2.button("👎", key=f"down{i}", on_click=rate, args=(i, "down"))

    q = st.chat_input("Ask a maritime safety or compliance question")
    if q:
        run_query(q)
        st.rerun()

# ---------------- analytics tab ----------------
with tab_stats:
    st.title("📊 Usage analytics")
    st.caption("Every question is logged locally in logs/queries.csv. These are the metrics a deployed version would track.")
    s = analytics.stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Questions asked", s["queries"])
    c2.metric("Refusal rate", f"{s['refusal_rate']:.0%}")
    c3.metric("Avg response time", f"{s['avg_latency']:.1f} s")
    c4.metric("Helpful rate", "n/a" if s["helpful_rate"] is None else f"{s['helpful_rate']:.0%}",
              help=f"Based on {s['feedback_count']} ratings")
    st.subheader("Recent questions")
    if s["recent"]:
        st.dataframe(s["recent"])
    else:
        st.info("No questions logged yet. Ask something in the Assistant tab.")
