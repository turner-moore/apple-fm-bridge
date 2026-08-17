# Apple FM vs ollama benchmark

On-device `fm system` vs local ollama models. Latency in seconds (wall clock, model already warm where possible). `expect` is a cheap substring check, not a quality score.

Hardware: M1 Pro 16GB. FM uses the Neural Engine (no RAM cost); ollama models consume 5-8GB each.


## Latency (seconds)

| task | cat | fm-system | qwen2.5-coder:7b-32k | qwen2.5:7b-16k | gemma3:4b-32k | llama3.1:8b-32k |
|---|---|---|---|---|---|---|
| summarize | summary | 5.79 | 31.50 | 14.91 | 18.87 | 11.53 |
| classify | classification | 0.68 (PASS) | 0.43 (PASS) | 0.42 (PASS) | 0.57 (PASS) | 0.46 (PASS) |
| extract | extraction | 1.41 (PASS) | 1.83 (PASS) | 1.87 (PASS) | 1.29 (PASS) | 14.47 (PASS) |
| code_explain | coding | 2.02 | 1.67 | 1.73 | 8.54 | 3.01 |
| bash_gen | coding | 1.06 (PASS) | 0.85 (PASS) | 0.74 (PASS) | 0.85 (PASS) | 0.87 (PASS) |
| rewrite | rewrite | 0.94 | 0.77 | 0.66 | 1.36 | 0.90 |
| qa | qa | 0.57 (PASS) | 0.43 (miss) | 0.29 (PASS) | 11.12 (PASS) | 0.40 (PASS) |

## Average latency

| model | avg s |
|---|---|
| fm-system | 1.78 |
| qwen2.5-coder:7b-32k | 5.35 |
| qwen2.5:7b-16k | 2.95 |
| gemma3:4b-32k | 6.09 |
| llama3.1:8b-32k | 4.52 |

## Sample outputs (quality eyeball)


### summarize (summary)
> Summarize in one sentence: Spanning Tree Protocol prevents layer-2 loops by electing a root bridge and blocking redundant paths, recalculating when topology changes.

- **fm-system**: The Spanning Tree Protocol prevents layer-2 loops by electing a root bridge, blocking redundant paths, and recalculating the network topology when changes occur.
- **qwen2.5-coder:7b-32k**: The Spanning Tree Protocol (STP) prevents layer-2 loops by designating a root bridge and disabling redundant pathways, automatically recalculating routes upon any topology changes to ensure network s…
- **qwen2.5:7b-16k**: The Spanning Tree Protocol prevents layer-2 network loops by selecting a root bridge and blocking redundant paths, dynamically recalculating the spanning tree topology when network changes occur.
- **gemma3:4b-32k**: Spanning Tree Protocol ensures network stability by intelligently blocking redundant network paths to eliminate loops, dynamically adjusting to changes in the network topology.
- **llama3.1:8b-32k**: The Spanning Tree Protocol (STP) eliminates layer-2 network loops by selecting a root bridge and blocking redundant paths while dynamically recalculating the network's best path in response to topolo…

### classify (classification)
> Reply with one word only - positive, negative, or neutral: 'This router keeps dropping BGP sessions and it's driving me insane.'

- **fm-system**: Negative
- **qwen2.5-coder:7b-32k**: Negative
- **qwen2.5:7b-16k**: Negative
- **gemma3:4b-32k**: Negative
- **llama3.1:8b-32k**: Negative.

### extract (extraction)
> From 'Contact Jane Doe at jane@acme.io or 555-0142', output only this JSON: {"name":..,"email":..,"phone":..}

- **fm-system**: ```json { "name": "Jane Doe", "email": "jane@acme.io", "phone": "555-0142" } ```
- **qwen2.5-coder:7b-32k**: ```json { "name": "Jane Doe", "email": "jane@acme.io", "phone": "555-0142" } ```
- **qwen2.5:7b-16k**: ```json { "name": "Jane Doe", "email": "jane@acme.io", "phone": "555-0142" } ```
- **gemma3:4b-32k**: ```json {"name": "Jane Doe", "email": "jane@acme.io", "phone": "555-0142"} ```
- **llama3.1:8b-32k**: Here is the code to extract the desired information into a JSON object: ```json { "name": "Jane Doe", "email": "jane@acme.io", "phone": "555-0142" } ``` However, since you asked for a code snippet th…

### code_explain (coding)
> Explain in one sentence what this does: grep -rl 'TODO' . | xargs sed -i '' 's/TODO/DONE/g'

- **fm-system**: This command searches for all files in the current directory containing "TODO" (with recursive depth) and modifies each occurrence of "TODO" to "DONE" in-place using sed.
- **qwen2.5-coder:7b-32k**: This command searches for all files containing the string "TODO" recursively starting from the current directory, and then replaces each instance of "TODO" with "DONE" in those files.
- **qwen2.5:7b-16k**: This command searches for all files in the current directory and its subdirectories containing the string "TODO", then replaces all occurrences of "TODO" with "DONE" in those files.
- **gemma3:4b-32k**: This command recursively searches for the string "TODO" within the current directory and all its subdirectories, then replaces every occurrence of "TODO" with "DONE" in each file found, modifying the…
- **llama3.1:8b-32k**: This command recursively searches for files containing the string "TODO" and replaces all occurrences with "DONE".

### bash_gen (coding)
> Give only a single bash one-liner (no explanation) to find files over 100MB under the current directory.

- **fm-system**: ```bash find . -type f -size +100M ```
- **qwen2.5-coder:7b-32k**: ```bash find . -type f -size +100M ```
- **qwen2.5:7b-16k**: `find . -type f -size +100M`
- **gemma3:4b-32k**: ```bash find . -type f -size +100M ```
- **llama3.1:8b-32k**: `find . -type f -size +100M`

### rewrite (rewrite)
> Rewrite more concisely, one line: 'In order to be able to make a determination regarding the matter, we will need to first gather all of the relevant information.'

- **fm-system**: "We need all relevant info to determine the matter."
- **qwen2.5-coder:7b-32k**: We need to gather all relevant info to make a determination.
- **qwen2.5:7b-16k**: We need to gather all relevant information first.
- **gemma3:4b-32k**: To determine this, we must first collect all relevant information.
- **llama3.1:8b-32k**: "We'll need to collect all relevant information before making a determination."

### qa (qa)
> In TCP/IP, what layer does a router primarily operate at? Answer in one short phrase.

- **fm-system**: Network layer
- **qwen2.5-coder:7b-32k**: Layer 3
- **qwen2.5:7b-16k**: Network Layer
- **gemma3:4b-32k**: Network Layer
- **llama3.1:8b-32k**: Network Layer.
