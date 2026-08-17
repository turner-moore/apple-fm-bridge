# apple-fm-bridge

[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2?style=flat-square)](https://modelcontextprotocol.io)
![macOS](https://img.shields.io/badge/macOS-26%2B-black?style=flat-square&logo=apple)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)

Talk to the language model built into macOS. It's free, runs on the Neural Engine, and never leaves your Mac.

```console
$ afm "explain what DNS does in one sentence"
DNS translates domain names into IP addresses to help devices locate web pages.

$ echo "This router keeps dropping BGP sessions and it's driving me insane." | afm "one word: positive, negative, or neutral"
Negative

$ afm --count "the quick brown fox jumps over the lazy dog"
10
```

No API key, no signup, no per-token bill. The tradeoff is a small context window (4096 tokens), so this is for small, frequent jobs, not long ones.

## Install

```sh
git clone https://github.com/turner-moore/apple-fm-bridge.git && cd apple-fm-bridge && \
claude mcp add -s user apple-fm -- /opt/homebrew/bin/python3 "$(pwd)/mcp-python/apple_fm_mcp.py"
```

That registers the MCP with Claude Code. Nothing to `pip install`, the server is pure Python stdlib. You need the `fm` CLI, which comes with macOS 26+ when Apple Intelligence is on.

Want the `afm` command on your PATH too:

```sh
ln -s "$(pwd)/bin/afm" /opt/homebrew/bin/afm
ln -s "$(pwd)/bin/fm-compress" /opt/homebrew/bin/fm-compress
```

<details>
<summary>Registering with a different MCP client</summary>

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
</details>

## The `afm` command

```console
$ afm "prompt"                          # ask
$ echo "text" | afm "instruction"       # pipe stdin in
$ afm -i "you are terse" "prompt"       # system message
$ afm --count "text"                    # token count
$ afm --image shot.png "what is this?"  # vision, small images
```

Structured output, give it a schema and it fills it:

```console
$ fm schema object --name Contact --string name --string email --string phone > contact.json
$ afm --schema contact.json "Contact Jane Doe at jane@acme.io or 555-0142"
{"phone": "555-0142", "name": "Jane Doe", "email": "jane@acme.io"}
```

> [!TIP]
> Too big for the window? `fm-compress` shrinks a file into a small digest first. A 12K-token doc came out ~170 tokens with the key facts kept. `afm` stops you at 3800 tokens and points you there.

## It's fast, and it's not eating your RAM

Same prompts on an M1 Pro 16GB, on-device vs local ollama models. Full tables and outputs in `bench/results.md`.

| model | avg latency | RAM |
|---|---|---|
| Apple FM (on-device) | 1.78s | ~0 |
| qwen2.5:7b | 2.95s | 5-8GB |
| llama3.1:8b | 4.52s | 5-8GB |
| gemma3:4b | 6.09s | 5-8GB |

The smallest model was the fastest, at no RAM cost, and matched the 7-8B models on classify, extract, bash, and Q&A. It loses on long inputs and real code generation. That's what the big models are for.

## Four ways in

- **`afm`**: the CLI above.
- **`apple-fm` MCP**: the same model as tools for Claude Code or any MCP client: `respond`, `extract`, `vision`, `token_count`, `available`, `compress`.
- **Apple Shortcuts**: run it from Spotlight or the menu bar, no terminal. See `shortcuts/README.md`.
- **`fm serve`**: `fm serve --socket /tmp/fm.sock` for an OpenAI-compatible `/v1/chat/completions` endpoint.

## Good to know

- 4096-token window. Small jobs only; `afm` gates you before you overflow it.
- On-device only. Private Cloud Compute isn't reachable from the CLI on this build.
- Needs macOS 26+ with Apple Intelligence enabled (that's what ships the `fm` CLI).
