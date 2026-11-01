from rag import retrieve, THRESHOLD

# (question, keyword that must appear in the source filename)
answerable = [
    ("What are the rules for a vessel overtaking another vessel?", "uscg"),
    ("What is the give-way vessel in a crossing situation?", "uscg"),
    ("What lights must a power-driven vessel under 50 metres show at night?", "uscg"),
    ("What is a safe speed under the collision regulations?", "uscg"),
    ("What sound signals are used in restricted visibility?", "uscg"),
    ("What are the responsibilities of a vessel in a narrow channel?", "uscg"),
    ("What is the rule for head-on situations between power-driven vessels?", "uscg"),
    ("What must a vessel do to avoid collision by taking action?", "uscg"),
    ("What are traffic separation schemes?", "uscg"),
    ("What day shapes does a vessel not under command display?", "uscg"),
    ("What lights does a sailing vessel show?", "uscg"),
    ("What does the look-out rule require?", "uscg"),
    ("What does SOLAS cover?", "solas"),
    ("What are the requirements for lifesaving appliances on ships?", "solas"),
    ("What does SOLAS say about fire protection?", "solas"),
    ("What is the purpose of the SOLAS convention?", "solas"),
    ("What does MARPOL regulate?", "marpol"),
    ("What are the annexes of MARPOL?", "marpol"),
    ("How does MARPOL control oil pollution from ships?", "marpol"),
    ("What does MARPOL say about air pollution from ships?", "marpol"),
]

unanswerable = [
    "What is the capital of France?",
    "How do I bake a chocolate cake?",
    "What are the rules for commercial aircraft landing?",
    "Who won the football world cup in 2018?",
]

hits = 0
for q, kw in answerable:
    res = retrieve(q)
    ok = any(kw in c["src"].lower() for c, _ in res)
    hits += ok
    print(("PASS" if ok else "FAIL"), "|", q, "| top score", round(res[0][1], 2))
print(f"\nRetrieval hit rate: {hits}/{len(answerable)} = {hits/len(answerable):.0%}")

refused = 0
for q in unanswerable:
    top = retrieve(q)[0][1]
    ok = top < THRESHOLD
    refused += ok
    print(("REFUSED" if ok else "ANSWERED (bad)"), "|", q, "| top score", round(top, 2))
print(f"Correct refusals: {refused}/{len(unanswerable)} = {refused/len(unanswerable):.0%}")
