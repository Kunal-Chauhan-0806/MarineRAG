import csv, os
from rag import retrieve, THRESHOLD

KW = {"COLREGs": "uscg", "SOLAS": "solas", "MARPOL": "marpol"}

answerable = [
    ("What are the rules for a vessel overtaking another vessel?", "COLREGs"),
    ("What is the give-way vessel in a crossing situation?", "COLREGs"),
    ("What lights must a power-driven vessel under 50 metres show at night?", "COLREGs"),
    ("What is a safe speed under the collision regulations?", "COLREGs"),
    ("What sound signals are used in restricted visibility?", "COLREGs"),
    ("What are the responsibilities of a vessel in a narrow channel?", "COLREGs"),
    ("What is the rule for head-on situations between power-driven vessels?", "COLREGs"),
    ("What must a vessel do to avoid collision by taking action?", "COLREGs"),
    ("What are traffic separation schemes?", "COLREGs"),
    ("What day shapes does a vessel not under command display?", "COLREGs"),
    ("What lights does a sailing vessel show?", "COLREGs"),
    ("What does the look-out rule require?", "COLREGs"),
    ("What does SOLAS cover?", "SOLAS"),
    ("What are the requirements for lifesaving appliances on ships?", "SOLAS"),
    ("What does SOLAS say about fire protection?", "SOLAS"),
    ("What is the purpose of the SOLAS convention?", "SOLAS"),
    ("What does MARPOL regulate?", "MARPOL"),
    ("What are the annexes of MARPOL?", "MARPOL"),
    ("How does MARPOL control oil pollution from ships?", "MARPOL"),
    ("What does MARPOL say about air pollution from ships?", "MARPOL"),
]

off_topic = [
    "What is the capital of France?",
    "How do I bake a chocolate cake?",
    "What are the rules for commercial aircraft landing?",
    "Who won the football world cup in 2018?",
    "Explain the rules of cricket.",
    "What is the GDP of India?",
    "How do I treat a fever at home?",
    "What is the best way to learn Python programming?",
]

# Maritime topics that are NOT in the loaded documents (hard negatives)
hard_negatives = [
    "What are the STCW minimum rest hour requirements for seafarers?",
    "What does the ISM Code require for safety management audits?",
    "What are the IMSBC Code rules for carrying bulk cargo?",
    "What penalties does the Indian Merchant Shipping Act impose?",
]

rows = []
print("=== Retrieval test (answerable questions) ===")
ranks, scores = [], []
for q, doc in answerable:
    res = retrieve(q, k=4)
    rank = next((i + 1 for i, (c, _) in enumerate(res) if KW[doc] in c["src"].lower()), None)
    ranks.append(rank)
    scores.append(res[0][1])
    print(("PASS" if rank else "FAIL"), f"| rank {rank} | top {res[0][1]:.2f} | {doc} | {q}")
    rows.append(["answerable", doc, q, rank or "", round(res[0][1], 3), ""])

n = len(answerable)
hit1 = sum(1 for r in ranks if r == 1)
hit4 = sum(1 for r in ranks if r)
mrr = sum(1 / r for r in ranks if r) / n
print(f"\nHit@1: {hit1}/{n} = {hit1/n:.0%}   Hit@4: {hit4}/{n} = {hit4/n:.0%}   MRR: {mrr:.3f}")

print("\nBy document:")
for doc in KW:
    idx = [i for i, (_, d) in enumerate(answerable) if d == doc]
    h = sum(1 for i in idx if ranks[i])
    print(f"  {doc}: {h}/{len(idx)}")

print(f"\nLowest score on a valid question: {min(scores):.2f}  (threshold = {THRESHOLD})")


def refusal_block(title, questions, label):
    print(f"\n=== {title} ===")
    top_scores, ok = [], 0
    for q in questions:
        top = retrieve(q, k=4)[0][1]
        top_scores.append(top)
        refused = top < THRESHOLD
        ok += refused
        print(("REFUSED" if refused else "ANSWERED (bad)"), f"| top {top:.2f} | {q}")
        rows.append([label, "", q, "", round(top, 3), "refused" if refused else "answered"])
    print(f"Correct refusals: {ok}/{len(questions)} = {ok/len(questions):.0%}  (highest score: {max(top_scores):.2f})")
    return top_scores


off_scores = refusal_block("Refusal test: off-topic questions", off_topic, "off_topic")
hard_scores = refusal_block("Refusal test: maritime but outside the documents (hard negatives)", hard_negatives, "hard_negative")

print("\n=== Threshold sweep ===")
print("threshold | answerable accepted | off-topic refused | hard negatives refused")
for t in [0.30, 0.34, 0.38, 0.42, 0.46, 0.50]:
    acc = sum(1 for s in scores if s >= t) / len(scores)
    off = sum(1 for s in off_scores if s < t) / len(off_scores)
    hard = sum(1 for s in hard_scores if s < t) / len(hard_scores)
    print(f"   {t:.2f}   |        {acc:4.0%}         |       {off:4.0%}        |        {hard:4.0%}")

os.makedirs("results", exist_ok=True)
with open("results/eval_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["type", "document", "question", "rank_of_correct_doc", "top_score", "decision"])
    w.writerows(rows)
print("\nSaved results/eval_results.csv")
