import streamlit as st
from rag import answer

st.set_page_config(page_title="MarineRAG", page_icon="⚓")
st.title("⚓ MarineRAG: Maritime Regulations Assistant")
st.caption("Answers come only from COLREGs, SOLAS and MARPOL documents, with page citations.")

q = st.text_input("Ask a maritime safety or compliance question")
if q:
    with st.spinner("Searching regulations..."):
        ans, hits = answer(q)
    st.write(ans)
    with st.expander("Sources retrieved"):
        for c, s in hits:
            st.markdown(f"**{c['src']} p.{c['page']}** (score {s:.2f})")
            st.caption(c["text"][:300])
