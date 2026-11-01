# MarineRAG: Business Case

## 1. The problem
Maritime work is governed by long international instruments (COLREGs, SOLAS, MARPOL and many more). Seafarers, cadets and ship managers lose time searching PDFs, and general AI chatbots can answer confidently but wrongly, which is dangerous in a safety-critical field.

## 2. Market opportunity
- The 2026 BIMCO-ICS Seafarer Workforce Report estimates about **2.57 million seafarers** serving on **85,148 merchant ships**.
- **India is now the 2nd-largest supplier**, with **311,936 seafarers (12.16%)**.
- The industry needs about **113,735 additional officers by 2030**, so training volume and regulatory-knowledge demand keep growing.
- Compliance pressure is real: the Paris MoU 2025 report records **16,474 port state inspections**, **9,879 with deficiencies** and **688 detentions**, with the detention rate rising to **4.18%** from 4.03% in 2024.

## 3. Target customers
| Segment | Need | Entry model |
|---|---|---|
| Cadets and junior officers | Fast, cited answers for exam prep and onboard work | Freemium, then monthly subscription |
| Maritime training institutes | Study support for large batches | Per-seat licence |
| Ship managers and crewing companies | Compliance support onboard, often with poor connectivity | Per-vessel annual licence (offline edition) |
| Consultants and surveyors | Quick lookup during inspection preparation | Subscription / API |

## 4. Value proposition
1. Every answer is cited to a document and page, so it can be verified.
2. It refuses to guess when the answer is not in the documents.
3. It runs **locally and offline**, which suits ships and keeps company data private.
4. No per-query API cost on the local edition.

## 5. Revenue model (illustrative assumptions)
| Stream | Price assumption |
|---|---|
| Cadet Pro | INR 199 per user per month |
| Institute licence | INR 99 per student seat per month (200 seats per institute) |
| Fleet licence | INR 60,000 per vessel per year |

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Paying cadets | 1,500 | 6,000 | 15,000 |
| Institutes | 5 | 25 | 80 |
| Vessels | 10 | 60 | 250 |
| Revenue (INR) | 53.7 lakh | 2.39 crore | 6.98 crore |
| Operating cost (INR) | 52 lakh | 1.5 crore | 3.8 crore |
| Operating profit (INR) | 1.7 lakh | 88.7 lakh | 3.18 crore |

These are planning assumptions, not forecasts. Year 3 paying cadets equal about 4.8% of India's seafarer workforce.

**Unit economics (assumed):** acquisition cost INR 300 per cadet through institutes and campus channels; average retention 8 months gives lifetime value of about INR 1,592, a ratio of roughly 5.3 to 1.

## 6. Competition
| Alternative | Weakness MarineRAG addresses |
|---|---|
| General AI chatbots | No guaranteed source, no refusal, needs internet |
| Manual PDF search | Slow, no natural-language questions |
| Publisher portals and e-learning | Costly, closed, not conversational |

## 7. Go-to-market
1. **Pilot** with 2 to 3 maritime training institutes in the Mumbai region and collect helpfulness ratings.
2. **Expand** to crewing and ship management companies with the offline edition.
3. **Scale** with an API for crewing and training software, and add more conventions.

## 8. Key metrics
Weekly active users, helpful rate (from the 👍 / 👎 buttons), refusal rate, retrieval hit rate, response time, paid conversion, monthly churn. The analytics tab in the app already tracks the first five.

## 9. Risks and mitigation
| Risk | Mitigation |
|---|---|
| Wrong answer in a safety context | Citations, refusal threshold, confidence level, clear disclaimer, human verification |
| Copyright of official IMO texts | Licence the content or use publisher partnerships; prototype uses public summaries |
| Outdated regulations | Version tagging and scheduled content updates |
| Small local model quality | Evaluate larger models; offer hosted option |
| Hard negatives scoring above threshold | Better calibration and re-ranking (see evaluation) |

## 10. Roadmap
Add full SOLAS and MARPOL texts and DG Shipping circulars; hybrid keyword plus vector search; re-ranker; multilingual support; mobile and offline packaging; automated answer-faithfulness scoring.

## Sources
BIMCO and ICS, Seafarer Workforce Report 2026; Paris MoU on Port State Control, Annual Report 2025.
