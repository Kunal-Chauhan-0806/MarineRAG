# MarineRAG: Maritime Regulations Assistant

A Retrieval-Augmented Generation (RAG) system that answers maritime safety questions
from COLREGs, SOLAS and MARPOL documents, with page-level citations and a refusal
when the answer is not in the documents.

## Stack
Python, sentence-transformers (all-MiniLM-L6-v2), FAISS, Ollama (llama3.2), Streamlit

## Run
    pip install sentence-transformers faiss-cpu pypdf openai streamlit numpy
    ollama pull llama3.2
    # put PDFs in data/
    streamlit run app.py

## Evaluation
    python3 eval.py
Retrieval hit rate: 20/20. Correct refusals on off-topic questions: 4/4.
