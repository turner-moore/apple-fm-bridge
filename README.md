# apple-fm-bridge

Your Mac already has a language model built in. `apple-fm-bridge` lets you actually use it, from your terminal, from Claude Code or any MCP client, or from an Apple Shortcut.

It's the Foundation Model that ships with Apple Intelligence. It runs on the Neural Engine, so it costs no money, sends nothing to a server, and barely touches your RAM. The catch is a small context window (4096 tokens), so it's for small, frequent jobs, not long ones.

## Why bother, when you already have Claude or ollama

Because for the small stuff, the built-in model is faster and free, and it isn't taking 5-8GB of RAM to sit there. Here's a run on an M1 Pro 16GB, on-device vs local ollama models, same prompts (`bench/results.md` has the full tables and the actual outputs):

| model | avg latency | RAM | quality on the mix |
|---|---|---|---|
| **Apple FM (on-device)** | **1.78s** | **~0** | matched the 7-8B models on classify, extract, bash, Q&A |
| qwen2.5:7b | 2.95s | 5-8GB | baseline |
| llama3.1:8b | 4.52s | 5-8GB | baseline |
| gemma3:4b | 6.09s | 5-8GB | baseline |

The smallest model was the fastest one, and it wasn't holding gigabytes hostage to do it. On a summarize task it finished in 5.8s while the ollama models took 12-31s. It loses on long inputs and hard code generation, that's what the bigger models are for.

Seven tasks on one machine isn't a leaderboard. It's enough to show where this model earns its place: short, high-volume work you'd otherwise pay a bigger model to do.

## Where it fits your flow

- **You're looping.** Classifying 400 log lines, tagging a folder of notes, extracting fields from a pile of records. Run the on-device model over each one instead of spending API calls.
- **You're feeding something big to a bigger model.** `fm-compress` shrinks a document first (a 12K-token doc came out a ~170-token digest, key facts kept), so the model that costs money reads less.
- **You want it out of the terminal entirely.** The Shortcuts run the model from Spotlight or the menu bar, no Claude, no code.

## Install

### Claude Code (copy-paste)

Paste this into your terminal. It clones and registers the MCP in one shot:

```sh
git clone https://github.com/turner-moore/apple-fm-bridge.git && cd apple-fm-bridge && \
claude mcp add -s user apple-fm -- /opt/homebrew/bin/python3 "$(pwd)/mcp-python/apple_fm_mcp.py"
```

Nothing to `pip install`, the MCP server is pure Python stdlib and `afm` is a shell script. You do need the **`fm` CLI**, which comes with macOS 26+ when Apple Intelligence is on.

Optional, put the CLIs on your PATH:

```sh
ln -s "$(pwd)/bin/afm" /opt/homebrew/bin/afm
ln -s "$(pwd)/bin/fm-compress" /opt/homebrew/bin/fm-compress
```

### Any other MCP client

Add this to your client's config (e.g. `claude_desktop_config.json`) with an absolute path:

```json
{
  "mcpServers": {
    "apple-fm": {
      "command": "/opt/homebrew/bin/python3",
      "args": ["/absolute/path/to/apple-fm-bridge/mcp-python/apple_fm_mcp.py"]
    }
  }
}
```

## Four ways to reach the model

1. **`afm` (CLI)**: the everyday one. `afm "prompt"`, pipe into it, add a system message (`-i`), force JSON out (`--schema`), read an image (`--image`), count tokens (`--count`). It stops you at 3800 tokens and points you at `fm-compress` when input is too big.
2. **`apple-fm` MCP**: the same model as tools for any MCP client: `respond`, `extract` (structured JSON), `vision`, `token_count`, `available`, `compress`. Pure stdlib Python, no dependencies.
3. **Apple Shortcuts**: run it with no terminal at all. See `shortcuts/README.md`.
4. **`fm serve`**: `fm serve --socket /tmp/fm.sock` gives you an OpenAI-compatible `/v1/chat/completions` endpoint for any OpenAI client.

## What's in here

```
bin/afm          CLI wrapper around the model, with a token pre-flight gate
bin/fm-compress  shrink a big file to a small digest (map-reduce, lossy)
mcp-python/      the apple-fm MCP server (stdlib only)
shortcuts/       standalone Apple Shortcuts
bench/           the benchmark script and results.md
```

## Limits, so you're not surprised

- **4096-token context.** Small jobs only. `afm` gates you before you overflow it.
- **Weaker on hard code generation** than a 7-8B model. Fine for one-liners and explanations, not for writing a module.
- **On-device only.** The cloud tier (Private Cloud Compute) isn't reachable from the CLI on this build, so everything here runs locally.

Requires macOS 26+ with Apple Intelligence enabled (that's what provides the `fm` CLI).
