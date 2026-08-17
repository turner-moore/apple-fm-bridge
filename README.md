# apple-fm-bridge

Surfaces for using Apple's **free, on-device Foundation Model** on macOS 26+ with Apple
Intelligence, so you can run work locally for free instead of hitting a paid API. Built 2026-06-17.

The on-device model (`system`) is free, has no quota or rate limit, and runs on the
Neural Engine, so it uses essentially no RAM and competes with nothing. Its limits:
a **4096-token context window** and weaker hard-coding ability than the local ollama
7-8B models. The cloud tier (`pcc`, Private Cloud Compute) is **not reachable from the
CLI** on this build, so everything here uses the on-device model.

Verified on this machine (2026-06-17): warm latency ~0.5s, cold ~6.7s, no per-call
cold-load penalty (unlike ollama, which costs 10-30s to load a model). On short
classify / extract / summarize / Q&A / bash tasks the 3B model matched the ollama
7-8B models on quality. See `bench/results.md`.

## Where it fits

| Tier | Engine | Cost | Use for |
|---|---|---|---|
| 0 | Apple on-device FM | free, ~0 RAM | short summaries, classification, extraction, quick Q&A, simple bash, rewrites, small-image OCR, chunk-summarization |
| 1 | ollama 7-8B | free, 5-8GB RAM | real coding, longer context (16-32K), stronger reasoning |
| 2 | A hosted model (paid API) | per-use cost | orchestration, multi-tool workflows, the top quality bar |

## What's here

```
bin/afm            friendly wrapper around `fm respond` with a 4096-token pre-flight gate
bin/fm-compress    map-reduce summarizer: shrink a big file to a small digest (lossy)
mcp-python/        zero-dependency stdio MCP (apple-fm) exposing the model as tools
bench/             FM-vs-ollama benchmark harness + results.md
shortcuts/         standalone Apple Shortcuts (zero-Claude) - see shortcuts/README.md
```

## The four access surfaces

1. **`afm` (Bash/CLI)** - on PATH at `/opt/homebrew/bin/afm`.
   - `afm "prompt"`, `echo content | afm "instruction"`, `afm -i "system" "..."`,
     `afm --schema spec.json "..."`, `afm --image shot.png "..."`,
     `afm --permissive "rewrite ..."`, `afm --count "..."`, `afm --json "..."`, `afm --warm`.
   - Gates input at 3800 tokens (4096 window minus output room) and points at `fm-compress`.

2. **`apple-fm` MCP** (`mcp__apple-fm__*`) - registered in `~/.claude.json`.
   - Tools: `respond`, `extract` (structured JSON), `vision`, `token_count`, `available`, `compress`.
   - Pure stdlib Python, shells out to `fm`. Registered with:
     `claude mcp add -s user apple-fm -- /opt/homebrew/bin/python3 .../mcp-python/apple_fm_mcp.py`

3. **Apple Shortcuts** - run the model with no terminal and no Claude. See `shortcuts/README.md`.

4. **`fm serve`** (bonus) - `fm serve --socket /tmp/fm.sock` exposes an OpenAI-compatible
   `/v1/chat/completions` API for any OpenAI client (LangChain, IDE tools, etc.).

## Token-savings reality (honest)

Offloading a tiny one-off to `afm` inside a Claude turn still costs a tool round-trip,
so it is not always a net win. The real wins:
- **Volume**: loop `afm` over many small items instead of asking Claude.
- **Preprocessing**: `fm-compress` a big input before Claude reads it (e.g. a 12K-token
  doc became a ~170-token digest, ~41x smaller, with key facts preserved).
- **Self-serve**: the Shortcuts and `afm` are zero-Claude entirely.
