# RFC-002: Lightweight Local Hugging Face Models

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-07-29 |
| Owners | Project maintainer |
| Amends | RFC-001 model providers, local deployment, and vector dimensions |

## 1. Context

RFC-001 selected Ollama with `nomic-embed-text` and `qwen2.5:7b` for local
confidential mode. That design protected document privacy but imposed a large
download and memory requirement for a portfolio project intended to run at
zero mandatory cash cost.

The model-provider interfaces, citation validator, artifact schemas, hybrid
retrieval, and privacy router already separate model execution from product
policy. The local implementation can therefore become lighter without changing
the user database authorization contract or allowing confidential data to
leave the machine.

## 2. Decision

Local confidential mode uses models downloaded from Hugging Face and executed
inside the FastAPI process:

| Task | Model | Output |
| --- | --- | --- |
| Semantic embeddings | `sentence-transformers/all-MiniLM-L6-v2` | 384-dimensional normalized vectors |
| Bounded text generation | `google/flan-t5-small` | Concise plain text |

The dependencies are provided by the optional Python `local-models` extra. They
are imported lazily so unit tests and the synthetic public demo do not download
or load model weights.

The application, not the generator:

- selects citation IDs from the retrieved tenant-scoped allowlist;
- constructs versioned artifact JSON;
- validates abstention and evidence requirements;
- rejects unsafe or structurally invalid output; and
- persists only validated results.

The small generator is never treated as an authorization, citation-selection,
or schema-validation authority.

## 3. Privacy and deployment

- Model weights may be downloaded from Hugging Face, but document text and
  prompts are processed locally.
- There is no automatic hosted-inference fallback.
- Gemini remains restricted to fictional `synthetic_demo` workspaces.
- The anonymous public demo remains deterministic and read-only and does not
  import the optional local-model packages.
- Telemetry continues to exclude prompts, completions, document bodies, tokens,
  credentials, and signed URLs.

## 4. Vector migration

MiniLM produces 384-dimensional vectors, while RFC-001 used 768 dimensions.
Migration `0014_huggingface_minilm_embeddings.sql` therefore:

1. marks existing artifact evidence pointers as missing;
2. removes derived chunks but retains original source objects and metadata;
3. changes the pgvector column to `vector(384)`;
4. recreates the HNSW index; and
5. queues retained sources for explicit re-indexing.

Embeddings from different models are not truncated, padded, or relabeled.
Re-indexing also updates the recorded provider and model on each document
version.

## 5. Quality contract

The existing deterministic retrieval report remains a reproducible regression
baseline, not a MiniLM or FLAN-T5 quality claim. Before release:

- re-index the synthetic evaluation corpus with MiniLM;
- record Recall@10, MRR, and nDCG under a new provider report;
- measure citation precision and abstention with FLAN-T5-small;
- retain deterministic prompt-injection and tenant-isolation tests; and
- record the hardware profile and cold-model latency.

If FLAN-T5-small cannot satisfy the frozen answer-quality thresholds, the
provider interface may add an optional sub-billion-parameter local generator.
That change must not weaken the local-only privacy boundary or make the public
demo depend on model hosting.

## 6. Consequences

### Positive

- No Ollama daemon or multi-gigabyte 7B model is required.
- The default local models are CPU-capable and free to download.
- Citation and artifact correctness remain deterministic application concerns.
- Public images and CI remain small because model packages are optional.

### Negative

- FLAN-T5-small has limited context and generation quality.
- The first local request includes model-download and load latency.
- Existing derived embeddings must be regenerated.
- Native Python ML dependencies add platform-specific installation weight.

## 7. Superseded RFC-001 statements

RFC-001 remains frozen as the original V1 decision record. Its statements that
Ollama is the default local provider, that local Compose requires Ollama, and
that embeddings have 768 dimensions are superseded only by this amendment. All
other RFC-001 security, tenancy, deletion, deployment, and synthetic-demo
constraints remain in force.
