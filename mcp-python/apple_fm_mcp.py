#!/usr/bin/env python3
"""apple-fm MCP server: exposes Apple's on-device Foundation Model as MCP tools.

Zero dependencies (Python stdlib only) on purpose: it just shells out to the
native `fm` CLI, so there is no pip install, no venv coupling, and nothing that
can drift against the system's framework Python.

Transport: newline-delimited JSON-RPC 2.0 over stdio (the MCP stdio transport).
Everything non-protocol goes to stderr; stdout carries only JSON-RPC messages.

Tools:
  respond(prompt, instructions?, permissive?, greedy?)  -> text
  extract(text, fields, instruction?)                   -> JSON (structured)
  vision(image_path, prompt)                            -> text (small images)
  token_count(text)                                     -> int
  available()                                           -> availability JSON
  compress(path, target_tokens?)                        -> digest (via fm-compress)

The on-device model is free and unlimited (no quota); ~4096-token window.
"""
import json
import os
import subprocess
import sys
import tempfile

FM_BIN = os.environ.get("FM_BIN", "/usr/bin/fm")
COMPRESS_BIN = os.environ.get(
    "FM_COMPRESS_BIN",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "fm-compress"),
)
CALL_TIMEOUT = int(os.environ.get("APPLE_FM_TIMEOUT", "90"))
SERVER_NAME = "apple-fm"
SERVER_VERSION = "0.1.0"
ANSI = __import__("re").compile(r"\x1b\[[0-9;]*m")


def log(*a):
    print(f"[{SERVER_NAME}]", *a, file=sys.stderr, flush=True)


def run_fm(args, timeout=CALL_TIMEOUT):
    """Run the fm CLI; return (ok, text). Never raises."""
    try:
        r = subprocess.run([FM_BIN, *args], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return False, f"fm CLI not found at {FM_BIN} (needs macOS 26+ with Apple Intelligence)"
    except subprocess.TimeoutExpired:
        return False, f"fm timed out after {timeout}s"
    except Exception as e:  # defensive: surface, never crash the server
        return False, f"fm invocation failed: {e}"
    out = ANSI.sub("", (r.stdout or "").strip())
    err = ANSI.sub("", (r.stderr or "").strip())
    if r.returncode != 0:
        return False, err or out or f"fm exited {r.returncode}"
    return True, out or err


# ---- tool implementations -------------------------------------------------

def tool_respond(args):
    prompt = (args.get("prompt") or "").strip()
    if not prompt:
        return False, "respond: 'prompt' is required"
    cmd = ["respond", "--no-stream"]
    if args.get("instructions"):
        cmd += ["--instructions", args["instructions"]]
    if args.get("permissive"):
        cmd += ["--guardrails", "permissive-content-transformations"]
    if args.get("greedy"):
        cmd += ["--greedy"]
    cmd.append(prompt)
    return run_fm(cmd)


_TYPE_FLAG = {"string": "--string", "int": "--int", "integer": "--int",
              "number": "--number", "float": "--number", "boolean": "--boolean", "bool": "--boolean"}


def tool_extract(args):
    text = (args.get("text") or "").strip()
    fields = args.get("fields") or []
    if not text:
        return False, "extract: 'text' is required"
    if not fields:
        return False, "extract: 'fields' (list of {name,type}) is required"
    # Build an fm schema via `fm schema object`, then feed it to respond --schema.
    schema_cmd = ["schema", "object", "--name", args.get("name", "Extraction")]
    for f in fields:
        name = f.get("name")
        ftype = (f.get("type") or "string").lower()
        flag = _TYPE_FLAG.get(ftype, "--string")
        if not name:
            return False, f"extract: field missing 'name': {f}"
        schema_cmd += [flag, name]
    ok, schema = run_fm(schema_cmd, timeout=15)
    if not ok:
        return False, f"extract: could not build schema: {schema}"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        tf.write(schema)
        schema_path = tf.name
    try:
        instr = args.get("instruction", "Extract the requested fields from the text.")
        prompt = f"{instr}\n\nText:\n{text}"
        ok, out = run_fm(["respond", "--no-stream", "--schema", schema_path, prompt])
    finally:
        try:
            os.unlink(schema_path)
        except OSError:
            pass
    return ok, out


def tool_vision(args):
    image = (args.get("image_path") or "").strip()
    prompt = (args.get("prompt") or "Describe this image.").strip()
    if not image:
        return False, "vision: 'image_path' is required"
    if not os.path.exists(image):
        return False, f"vision: image not found: {image}"
    return run_fm(["respond", "--no-stream", "--image", image, "--text", prompt])


def tool_token_count(args):
    text = args.get("text") or ""
    if not text:
        return False, "token_count: 'text' is required"
    ok, out = run_fm(["token-count", text], timeout=15)
    if not ok:
        return False, out
    digits = "".join(ch for ch in out if ch.isdigit())
    return True, digits or out


def tool_available(args):
    ok, out = run_fm(["available"], timeout=15)
    # `fm available` prints a status line for system + (unavailable) pcc; pass it through.
    return True, out if out else "system model status unknown"


def tool_compress(args):
    path = (args.get("path") or "").strip()
    if not path:
        return False, "compress: 'path' is required"
    if not os.path.exists(COMPRESS_BIN):
        return False, f"compress: fm-compress not found at {COMPRESS_BIN} (Phase 4 artifact)"
    cmd = [COMPRESS_BIN, path]
    tt = args.get("target_tokens")
    if tt:
        cmd += ["--target", str(tt)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as e:
        return False, f"compress failed: {e}"
    if r.returncode != 0:
        return False, ANSI.sub("", (r.stderr or "").strip()) or "compress error"
    return True, ANSI.sub("", (r.stdout or "").strip())


TOOLS = {
    "respond": {
        "impl": tool_respond,
        "description": "Generate a response from Apple's free on-device model. Best for short tasks (classify, summarize, quick Q&A, short rewrite) that fit a 4096-token window. Use 'permissive' for rewrite/transform tasks.",
        "schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt to respond to."},
                "instructions": {"type": "string", "description": "Optional system instructions."},
                "permissive": {"type": "boolean", "description": "Use permissive-content-transformations guardrail (for rewrites/transforms)."},
                "greedy": {"type": "boolean", "description": "Greedy (deterministic) sampling."},
            },
            "required": ["prompt"],
        },
    },
    "extract": {
        "impl": tool_extract,
        "description": "Extract structured fields from text as JSON, using the on-device model's guided generation. Provide 'fields' as a list of {name, type} where type is string|int|number|boolean.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Source text to extract from."},
                "fields": {
                    "type": "array",
                    "description": "Fields to extract.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string", "enum": ["string", "int", "number", "boolean"]},
                        },
                        "required": ["name"],
                    },
                },
                "instruction": {"type": "string", "description": "Optional extraction instruction."},
                "name": {"type": "string", "description": "Optional schema/object name."},
            },
            "required": ["text", "fields"],
        },
    },
    "vision": {
        "impl": tool_vision,
        "description": "Ask the on-device model about a (small) image: OCR, alt text, simple Q&A. For dense screenshots/terminals prefer the ollama qwen2.5vl model instead.",
        "schema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Absolute path to an image file."},
                "prompt": {"type": "string", "description": "What to ask about the image."},
            },
            "required": ["image_path"],
        },
    },
    "token_count": {
        "impl": tool_token_count,
        "description": "Count how many tokens a string is for the on-device model (window is 4096). Use to decide whether input fits before calling respond.",
        "schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    "available": {
        "impl": tool_available,
        "description": "Check on-device (and PCC) model availability.",
        "schema": {"type": "object", "properties": {}},
    },
    "compress": {
        "impl": tool_compress,
        "description": "Compress a large file into a shorter digest using the on-device model (chunk + map-summarize). Lossy: use for overview/summary, not when exact content matters.",
        "schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file to compress."},
                "target_tokens": {"type": "integer", "description": "Approx target size of the digest."},
            },
            "required": ["path"],
        },
    },
}


# ---- JSON-RPC plumbing ----------------------------------------------------

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def reply(req_id, result):
    send({"jsonrpc": "2.0", "id": req_id, "result": result})


def reply_error(req_id, code, message):
    send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def handle(msg):
    method = msg.get("method")
    req_id = msg.get("id")
    is_request = req_id is not None

    if method == "initialize":
        client_ver = (msg.get("params") or {}).get("protocolVersion")
        reply(req_id, {
            "protocolVersion": client_ver or "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
        return
    if method in ("notifications/initialized", "initialized"):
        return  # notification, no reply
    if method == "ping":
        if is_request:
            reply(req_id, {})
        return
    if method == "tools/list":
        tools = [{
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["schema"],
        } for name, spec in TOOLS.items()]
        reply(req_id, {"tools": tools})
        return
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        spec = TOOLS.get(name)
        if not spec:
            reply(req_id, {"content": [{"type": "text", "text": f"unknown tool: {name}"}], "isError": True})
            return
        try:
            ok, text = spec["impl"](args)
        except Exception as e:  # never let a tool crash the server
            ok, text = False, f"tool '{name}' raised: {e}"
        reply(req_id, {"content": [{"type": "text", "text": text}], "isError": not ok})
        return

    if is_request:
        reply_error(req_id, -32601, f"method not found: {method}")


def main():
    log(f"starting (fm={FM_BIN})")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            handle(msg)
        except Exception as e:
            log("handler error:", e)
    log("stdin closed, exiting")


if __name__ == "__main__":
    main()
