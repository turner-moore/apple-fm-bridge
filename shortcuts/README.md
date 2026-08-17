# Apple On-Device AI Shortcuts

Three macOS Shortcuts that query Apple's on-device Foundation Model (Apple Intelligence) directly, with zero Claude involvement. The point is to offload short text tasks to the free, on-device model and save Claude usage.

Built and signed on macOS 27.0 (build 26A5353q), Apple Silicon, on 2026-06-17.

## Mechanism: native "Use Model" action (not Run Shell Script)

All three shortcuts use the **native Apple Intelligence action** `is.workflow.actions.askllm` (shown in the Shortcuts editor as **Use Model**), targeting the on-device model:

- `WFLLMModel = "Apple Intelligence"` (the on-device Foundation Model; no Private Cloud Compute, no network)
- `WFGenerativeResultType = "Text"`

This was chosen over a `Run Shell Script` action that shells out to `/usr/bin/fm respond --no-stream`. Both reach the same on-device model, but the native action is the cleaner fit: no shell, no `PATH` fragility, and the answer flows directly into the next action as the **Response** variable. The `fm` CLI still works (verified: `/usr/bin/fm respond --no-stream 'Reply with exactly the word: PONG'` returns `PONG`); it just is not needed here.

### Does macOS 27 Shortcuts have a native on-device model action?

**Yes.** macOS 27 ships the **Use Model** action (`is.workflow.actions.askllm`). Setting its model to **Apple Intelligence** runs the prompt entirely on-device. That is the action all three of these shortcuts use, confirmed working at runtime (see Verification below).

## The three shortcuts

| # | Name | Variant | What it does |
|---|------|---------|--------------|
| 1 | `Ask On-Device AI` | Native Use Model | Prompts you for text, sends it to the on-device model, shows the answer (Quick Look / result sheet), and copies it to the clipboard. |
| 2 | `Summarize Clipboard (On-Device)` | Native Use Model | Reads the current clipboard text, asks the on-device model for a concise summary, shows it, and copies the summary back to the clipboard. |
| 3 | `Summarize Selection (On-Device)` | Native Use Model, **Quick Action** | A Services / share-sheet Quick Action: accepts selected text, summarizes it on-device, and shows the result. |

All three handle empty input gracefully:
- #1 shows a "No input" alert if you submit nothing.
- #2 shows a "Clipboard is empty" alert if there is no clipboard text.
- #3 shows a "No selection" alert if no text was passed in.

All user-visible text avoids em dashes.

## Files

Signed `.shortcut` files (open these in Shortcuts.app to import):

- `Ask On-Device AI.shortcut`
- `Summarize Clipboard (On-Device).shortcut`
- `Summarize Selection (On-Device).shortcut`

## Install

```sh
open -a Shortcuts "Ask On-Device AI.shortcut"
open -a Shortcuts "Summarize Clipboard (On-Device).shortcut"
open -a Shortcuts "Summarize Selection (On-Device).shortcut"
```

(All three were already imported into the library during the build.)

## How to test

### #1 and #2 from the CLI

```sh
# #2 is fully non-interactive. Set the clipboard, then run it.
printf '%s' "Some long passage you want summarized." | pbcopy
shortcuts run "Summarize Clipboard (On-Device)" --output-path /tmp/summary.txt --output-type public.plain-text
cat /tmp/summary.txt
```

Use `--output-path` + `--output-type public.plain-text` to capture the answer as clean text. Reading `pbpaste` also works (the shortcut copies the summary back), but the file channel avoids a race with macOS Universal Clipboard / clipboard managers.

**First-run latency:** the very first `Use Model` call after login can take ~15 to 20 seconds while the on-device model warms up. Subsequent calls return in roughly 5 to 8 seconds. If a CLI run seems to hang, give it ~30 seconds before assuming failure.

**#1 (`Ask On-Device AI`) is interactive and does not run headlessly.** It contains an "Ask for Input" prompt, so `shortcuts run "Ask On-Device AI"` will block waiting for a dialog that the CLI cannot answer (the prompt is internal input, not Shortcut Input, so `--input-path` does not feed it). Run #1 the normal way: from the Shortcuts app, Spotlight, or the menu bar. Its on-device model path is otherwise identical to the verified ones.

### #3 (the Quick Action) from the Services menu

`shortcuts run` cannot pass a text selection to a Quick Action, so test #3 the way it is meant to be used:

1. In any app, select some text (Notes, Mail, Safari, TextEdit, a webpage, etc.).
2. Right-click the selection (or open the app's **Services** submenu, or the **menu bar app name > Services** menu).
3. Choose **Summarize Selection (On-Device)**.
4. The on-device summary appears, and is also copied to the clipboard.

If it does not appear in the Services menu immediately:
- Open **System Settings > Keyboard > Keyboard Shortcuts > Services > Text** and confirm **Summarize Selection (On-Device)** is enabled.
- Quick Actions register from the share sheet / Services on first import; toggling it in that pane forces it to show.
- You can also run it from the Shortcuts app share sheet on selected text.

## Permissions

These shortcuts need only two grants, and there is no third-party or network access of any kind.

1. **Apple Intelligence (on-device model).** Already granted on this Mac. Verified: the Use Model action returned real on-device answers during the build (`PONG`, `Tokyo`, and correct summaries). The first-ever Use Model run shows a one-time enablement prompt; it has already been satisfied here.

2. **Clipboard access (per-shortcut privacy grant).** This is the one grant that may still need your approval, and it can only be approved by you in the GUI (there is no `shortcuts` CLI subcommand for privacy, confirmed). Verified state during the build:
   - `Summarize Clipboard (On-Device)`: clipboard access working (it read the clipboard and summarized it repeatedly with no prompt).
   - `Summarize Selection (On-Device)`: clipboard access **not yet granted**. A headless run reported: `This shortcut can't access "Clipboard". You can change this in the shortcut's privacy settings.` It writes the summary to the clipboard, so it needs this grant.
   - `Ask On-Device AI`: also writes the clipboard; approve the same prompt the first time you run it.

   **How to approve it:** run each shortcut once from the Shortcuts app (not the CLI). The first time it touches the clipboard, macOS shows "ShortcutName would like to paste from other apps" (or a clipboard-access prompt); click **Allow** / **Always Allow**. Alternatively, in the Shortcuts app, open each shortcut, click the info/settings control, and enable its clipboard privacy permission there. Once approved in the GUI, both GUI and CLI runs work without prompting.

   I cannot click these dialogs for you: clipboard/Apple Intelligence grants are user-consent (TCC) dialogs that macOS requires the actual user to approve. The build surfaced exactly which one is outstanding so you can approve it deliberately.

## Notes and caveats

- **On-device only.** The model is set to Apple Intelligence (on-device). Private Cloud Compute is not used and is not available from this path, which is intentional. Apple Intelligence must be enabled on the Mac (System Settings > Apple Intelligence and Siri) for the Use Model action to run.
- **~4096-token window.** The on-device Foundation Model has roughly a 4096-token context window. The summarize shortcuts work fine for typical clipboard and selection sizes (paragraphs to a few pages). Very long inputs may be truncated by the model; for large documents, summarize in chunks.
- **No Claude, no network.** None of these shortcuts call Claude, any cloud API, or any third-party service.
- **First-run consent.** The first time you run a Use Model action you may see a one-time Apple Intelligence enablement/consent prompt. Approve it once in the GUI; after that the CLI and Services runs proceed without prompting.

## Signing / install gotchas encountered

- Signed with the plugin pipeline (`shortcuts sign --mode anyone`); each signed file is ~23 KB (about 19 KB of that is the signature).
- **Output filename equals the display name** (no `_signed` suffix). Keep it that way; renaming the file does not rename the shortcut.
- **Duplicate names silently skip on import.** If a shortcut with the same name already exists in your library, re-importing the signed file is a no-op. The `shortcuts` CLI has no `import`, `delete`, or `rename` subcommand, so to replace one of these, delete the old entry in the Shortcuts app first, then re-open the `.shortcut`.
- **Verification artifacts:** two throwaway probe shortcuts named `FM Probe` and `Ask Probe` were created to test the model path headlessly and then deleted from disk. They may still appear in your Shortcuts library; delete them in-app if you want a clean list (the CLI cannot delete them).

## Verification (actual results from this build)

Captured with `shortcuts run ... --output-type public.plain-text` on 2026-06-17:

- **On-device model reachable** (probe, fixed prompt "Reply with exactly one word: PONG"): returned `PONG`.
- **#2 `Summarize Clipboard (On-Device)`** on a 434-character James Webb Space Telescope passage returned a correct concise summary (key facts retained: Dec 2021 launch, infrared, 6.5 m mirror of 18 gold-coated beryllium segments, L2 orbit ~1.5 million km from Earth), with the commentary stripped, in ~6 seconds.
- **#1 / #3 model path** (probe taking the question as input, identical Use Model wiring) for "what is the capital of Japan?" returned `The capital of Japan is Tokyo.` in ~7 seconds.
- **#1** confirmed to block under headless `shortcuts run` because of its interactive Ask prompt (expected; run it interactively).
