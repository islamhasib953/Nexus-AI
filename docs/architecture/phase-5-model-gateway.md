# Phase 5 — Model gateway and routing

## Registry

The registry is implemented in `apps/api/app/llm/registry.py`. Model selection is configuration-driven through `LLM_PRIMARY_MODEL_ID` and `LLM_FALLBACK_MODEL_IDS`; agents and API routes do not contain provider-specific calls.

| Registry ID | Provider | Provider model | Context setting | Structured output |
| --- | --- | --- | --- | --- |
| `mock-chat` | Mock | `mock-chat` | 8,192 | Yes |
| `groq-gpt-oss-20b` | Groq | `openai/gpt-oss-20b` | 131,072 | Yes |
| `hf-qwen3` | Hugging Face | `Qwen/Qwen3-32B` | 32,768 | Yes |
| `ollama-qwen3` | Ollama | `qwen3:8b` | 32,768 | Yes |

Context settings are conservative routing configuration, not contractual provider guarantees. Operators must verify model availability and account limits before selecting a production default.

## Routing policy

1. The primary model is read from configuration.
2. Each candidate is checked against the tenant and global daily budgets before invocation.
3. Paid candidates are skipped unless `LLM_ALLOW_PAID_FALLBACK=true`.
4. Provider failures use bounded retries and open an in-memory exponential-backoff circuit.
5. Only explicitly configured fallback IDs are tried.
6. If no candidate works, the run becomes `failed` with a durable event; no provider exception or secret reaches the client.

## Provider limitations

- Groq uses an OpenAI-compatible chat endpoint. Its organization/project limits can independently cap requests and tokens; consult [Groq rate limits](https://console.groq.com/docs/rate-limits). Structured output compatibility is model-dependent; strict structured output does not support streaming according to [Groq structured-output guidance](https://console.groq.com/docs/structured-outputs).
- Hugging Face Inference Providers supports OpenAI-compatible routing, but model/provider availability and pricing vary. The router exposes model-specific pricing metadata where available; see the [Hub API reference](https://huggingface.co/docs/inference-providers/hub-api). Structured requests should select a compatible model/provider pair rather than relying on automatic routing; see [HF structured outputs](https://huggingface.co/docs/inference-providers/en/guides/structured-output).
- Ollama is local and therefore has no provider token bill, but it depends on installed models, local hardware, and host availability. Its chat API supports JSON-schema `format`; see [Ollama structured outputs](https://ollama.com/blog/structured-outputs).

All cloud adapters require a secret supplied only through the environment. The repository has no provider key and does not make external inference calls during tests.
