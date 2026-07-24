# Self-hosted LLM worker

AI Cartoon Studio talks to a self-hosted OpenAI-compatible endpoint. The endpoint may run on a local workstation, Lightning AI, Google Colab, Kaggle, or a rented GPU server. The application does not call OpenAI.

## Supported servers

- vLLM
- llama.cpp `llama-server`
- Any compatible server exposing `/v1/models` and `/v1/chat/completions`

## Required application settings

```env
LLM_PROVIDER=local-openai-compatible
LLM_BASE_URL=https://your-private-tunnel.example/v1
LLM_API_KEY=replace-with-a-private-token
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
LLM_TIMEOUT_SECONDS=300
LLM_MAX_RETRIES=2
```

The provider is replaceable. Moving from Colab to Lightning or a dedicated GPU requires only changing these environment values.

## Lightning AI

1. Create a GPU Studio.
2. Clone the repository or copy `scripts/run_local_llm.sh`.
3. Set `MODEL_ID`, `LLM_API_KEY`, and optionally `VLLM_EXTRA_ARGS`.
4. Run the script.
5. Expose port `8001` privately through the platform networking controls.
6. Set the resulting endpoint in the application `.env` file.

Example:

```bash
export MODEL_ID=Qwen/Qwen2.5-7B-Instruct-AWQ
export LLM_API_KEY=a-long-random-token
bash scripts/run_local_llm.sh
```

## Colab

Open `notebooks/local_llm_colab.ipynb`. It installs vLLM, starts the server, validates it, and can create a temporary Cloudflare tunnel. Colab sessions are temporary, so the story jobs remain persisted in PostgreSQL and can be retried after a session restarts.

## Security

- Never expose the endpoint without a bearer token.
- Do not put the token in the repository.
- Keep PostgreSQL, Redis, media assets, and the dashboard outside Colab.
- Treat the tunnel URL as temporary infrastructure.
- Rotate the token after sharing logs or notebooks.

## Health check

The dashboard calls:

```text
GET /api/v1/llm/health
```

An offline model does not delete work. Story generation jobs remain queued or failed and can be retried after the worker becomes available.
