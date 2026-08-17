# apple-fm-bridge

**Use Apple's built-in, on-device AI from your terminal, from an MCP client, or from an Apple Shortcut.** It runs the free Foundation Model that ships with macOS, on the Neural Engine. No API key, no cloud round-trip, no per-token bill, and almost no RAM.

## Why you'd want it

- **Free.** No quota, no rate limit, no signup. The model is already on your Mac.
- **Private.** Prompts never leave the machine.
- **Light.** Runs on the Neural Engine, so it competes with nothing for memory.
- **Fast when warm.** ~0.5s warm, ~6.7s cold, and no per-call model reload.

Good for: summarizing, classifying, extracting fields, quick Q&A, small-image OCR, rewrites, shrinking a big document before a bigger model reads it. Taps out on: long inputs (**4096-token window**) and heavy coding, where a 7-8B local model or a hosted model wins.

## Quick start

```sh
afm "explain DNS in one sentence"
echo "$(pbpaste)" | afm "summarize this"
afm --schema fields.json "pull the name and date from this"
afm --image screenshot.png "what does this say?"
```

`afm` gates input at 3800 tokens (the 4096 window minus room to answer) and points you at `fm-compress` when something is too big.

## Four ways to use it

1. **`afm` (CLI)** — the everyday one. Prompt, pipe, add a system message (`-i`), force JSON (`--schema`), read an image (`--image`), count tokens (`--count`).
2. **`apple-fm` MCP** — exposes the model to any MCP client. Tools: `respond`, `extract` (structured JSON), `vision`, `token_count`, `available`, `compress`. Pure-stdlib Python, zero dependencies.
   ```sh
   claude mcp add -s user apple-fm -- /opt/homebrew/bin/python3 mcp-python/apple_fm_mcp.py
   ```
3. **Apple Shortcuts** — run the model with no terminal at all. See `shortcuts/README.md`.
4. **`fm serve`** — `fm serve --socket /tmp/fm.sock` gives you an OpenAI-compatible `/v1/chat/completions` endpoint for any OpenAI client.

## When it actually saves you money

Offloading one tiny call inside a bigger AI session can cost more than it saves (still a round-trip). The real wins:

- **Volume** — loop `afm` over many small items instead of asking a paid model each time.
- **Preprocessing** — `fm-compress` a large input first (a 12K-token doc became a ~170-token digest, ~41x smaller, key facts kept).
- **Self-serve** — the Shortcuts and `afm` need no other AI at all.

## What's in here

```
bin/afm          CLI wrapper around the model, with a token pre-flight gate
bin/fm-compress  shrink a big file to a small digest (map-reduce, lossy)
mcp-python/      the apple-fm MCP server (stdlib only)
shortcuts/       standalone Apple Shortcuts
bench/           benchmark harness + results.md (on-device vs local ollama)
```

## Requirements

macOS 26+ with Apple Intelligence enabled (provides the `fm` CLI and the Foundation Model). The cloud tier (Private Cloud Compute) isn't reachable from the CLI on this build, so everything here uses the on-device model.
