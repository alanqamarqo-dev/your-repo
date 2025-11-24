# Ollama tuning recommendations (for ~4GB GPU)

- Use quantized model variants (q4_K_M or q5_K_M) when available for the chosen model.
- Example: use a qwen2.5:7b-instruct-quantized (q4) build or a smaller 3B quantized model.
- Start Ollama with small worker batch and reduced context if memory constrained.
- Recommended model options in request payload:
  - temperature: 0.05-0.2
  - top_p: 0.3-0.9 (lower for deterministic short answers)
  - repeat_penalty: 1.05-1.2
  - max_tokens (or max_new_tokens): 256-512 depending on task
- Enable caching for repeated system prompts and shared instructions at the adapter level.
- If using Ollama CLI, prefer runner flags that enable int4/int8 quantization if supported.

Note: exact flags depend on model build and Ollama/runner version. Test latency and quality tradeoffs.
