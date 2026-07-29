# Evaluation Method

Dataset `1.0.0` contains thirty reviewed synthetic cases: twenty answerable,
five unanswerable, two contradictory, and three prompt-injection questions.

The committed retrieval report evaluates the twenty answerable cases and four
adversarial or contradiction cases that declare expected sources.

| Metric | Measured deterministic baseline |
| --- | ---: |
| Cases with expected sources | 24 |
| Recall@10 | 1.000 |
| MRR | 0.847 |
| Mean nDCG | 0.884 |

The deterministic hash embedding is a reproducible test baseline, not the
recommended production model. Rerun the gates with
`sentence-transformers/all-MiniLM-L6-v2` and `google/flan-t5-small` before
making model-quality claims.

Citation-precision and abstention metrics are implemented, but no generation
score is claimed until a lightweight Hugging Face run has been repeated and
reviewed. Security invariants remain deterministic and do not depend on model
output. Citation IDs and artifact structure are selected by application code
from the retrieved allowlist rather than trusted to the small generator.

Any change to the corpus, questions, chunker, embedding provider, RRF constant,
prompt, model, or citation validator requires a new report.
