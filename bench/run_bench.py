#!/usr/bin/env python3
"""Benchmark Apple's on-device Foundation Model (fm system) against the local
ollama models, on a fixed task mix.

Goal: produce data that decides which task types are genuinely better on FM
(free, no RAM, ~4K ctx) vs ollama (uses 5-8GB RAM, larger ctx, stronger coding).

No third-party deps: stdlib only. fm via subprocess, ollama via its HTTP API.
Runs model-by-model so ollama evicts the previous model before loading the next
(keeps RAM under the M1 Pro 16GB ceiling). Writes results.md next to this file.

Usage:
  python3 run_bench.py                 # default model set
  python3 run_bench.py --quick         # fm + 2 ollama models only
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
CALL_TIMEOUT = 120
HERE = Path(__file__).resolve().parent

# Task mix: kept small (well under the 4K on-device window) and representative
# of the kinds of tasks routed to a local model. `expect` is a cheap substring
# sanity check (case-insensitive); None means eyeball-only.
TASKS = [
    {"id": "summarize", "cat": "summary",
     "prompt": "Summarize in one sentence: Spanning Tree Protocol prevents layer-2 loops by electing a root bridge and blocking redundant paths, recalculating when topology changes.",
     "expect": None},
    {"id": "classify", "cat": "classification",
     "prompt": "Reply with one word only - positive, negative, or neutral: 'This router keeps dropping BGP sessions and it's driving me insane.'",
     "expect": "negative"},
    {"id": "extract", "cat": "extraction",
     "prompt": "From 'Contact Jane Doe at jane@acme.io or 555-0142', output only this JSON: {\"name\":..,\"email\":..,\"phone\":..}",
     "expect": "jane@acme.io"},
    {"id": "code_explain", "cat": "coding",
     "prompt": "Explain in one sentence what this does: grep -rl 'TODO' . | xargs sed -i '' 's/TODO/DONE/g'",
     "expect": None},
    {"id": "bash_gen", "cat": "coding",
     "prompt": "Give only a single bash one-liner (no explanation) to find files over 100MB under the current directory.",
     "expect": "find"},
    {"id": "rewrite", "cat": "rewrite",
     "prompt": "Rewrite more concisely, one line: 'In order to be able to make a determination regarding the matter, we will need to first gather all of the relevant information.'",
     "expect": None},
    {"id": "qa", "cat": "qa",
     "prompt": "In TCP/IP, what layer does a router primarily operate at? Answer in one short phrase.",
     "expect": "network"},
]

DEFAULT_MODELS = [
    ("fm-system", "fm"),
    ("qwen2.5-coder:7b-32k", "ollama"),
    ("qwen2.5:7b-16k", "ollama"),
    ("gemma3:4b-32k", "ollama"),
    ("llama3.1:8b-32k", "ollama"),
]
QUICK_MODELS = [
    ("fm-system", "fm"),
    ("qwen2.5-coder:7b-32k", "ollama"),
    ("gemma3:4b-32k", "ollama"),
]


def run_fm(prompt):
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            ["fm", "respond", "--no-stream", prompt],
            capture_output=True, text=True, timeout=CALL_TIMEOUT,
        )
        out = (r.stdout or "").strip() or (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        out = "<TIMEOUT>"
    except Exception as e:
        out = f"<ERROR: {e}>"
    return out, time.perf_counter() - t0


def run_ollama(model, prompt):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=CALL_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        out = (data.get("message", {}).get("content") or "").strip()
    except Exception as e:
        out = f"<ERROR: {e}>"
    return out, time.perf_counter() - t0


def one_line(s, n=110):
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="fm + 2 ollama models")
    args = ap.parse_args()
    models = QUICK_MODELS if args.quick else DEFAULT_MODELS

    # results[task_id][model] = (latency, output)
    results = {t["id"]: {} for t in TASKS}
    # Run model-by-model so ollama only holds one model in RAM at a time.
    for model, kind in models:
        print(f"== {model} ==", flush=True)
        for t in TASKS:
            if kind == "fm":
                out, dt = run_fm(t["prompt"])
            else:
                out, dt = run_ollama(model, t["prompt"])
            ok = ""
            if t["expect"]:
                ok = "PASS" if t["expect"].lower() in out.lower() else "miss"
            results[t["id"]][model] = (dt, out, ok)
            print(f"  {t['id']:<13} {dt:6.2f}s  {ok:<4} {one_line(out, 70)}", flush=True)

    # ---- write results.md ----
    lines = []
    lines.append("# Apple FM vs ollama benchmark\n")
    lines.append("On-device `fm system` vs local ollama models. Latency in seconds "
                 "(wall clock, model already warm where possible). `expect` is a cheap "
                 "substring check, not a quality score.\n")
    lines.append("Hardware: M1 Pro 16GB. FM uses the Neural Engine (no RAM cost); "
                 "ollama models consume 5-8GB each.\n")

    # latency table
    header = "| task | cat | " + " | ".join(m for m, _ in models) + " |"
    sep = "|" + "---|" * (len(models) + 2)
    lines.append("\n## Latency (seconds)\n")
    lines.append(header)
    lines.append(sep)
    for t in TASKS:
        row = [t["id"], t["cat"]]
        for m, _ in models:
            dt, _out, ok = results[t["id"]][m]
            cell = f"{dt:.2f}"
            if ok:
                cell += f" ({ok})"
            row.append(cell)
        lines.append("| " + " | ".join(row) + " |")

    # averages
    lines.append("\n## Average latency\n")
    lines.append("| model | avg s |")
    lines.append("|---|---|")
    for m, _ in models:
        avg = sum(results[t["id"]][m][0] for t in TASKS) / len(TASKS)
        lines.append(f"| {m} | {avg:.2f} |")

    # outputs appendix (for eyeballing quality)
    lines.append("\n## Sample outputs (quality eyeball)\n")
    for t in TASKS:
        lines.append(f"\n### {t['id']} ({t['cat']})")
        lines.append(f"> {t['prompt']}\n")
        for m, _ in models:
            _dt, out, _ok = results[t["id"]][m]
            lines.append(f"- **{m}**: {one_line(out, 200)}")

    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {HERE / 'results.md'}")


if __name__ == "__main__":
    sys.exit(main())
