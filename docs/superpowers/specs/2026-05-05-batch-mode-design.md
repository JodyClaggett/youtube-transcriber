# Batch Mode — Design Spec

**Date:** 2026-05-05
**Status:** Approved

---

## Context

The tool currently processes one YouTube URL at a time via an interactive prompt. Users want to submit multiple URLs at once without re-running the script. This adds a batch mode: pass a text file of URLs as a command-line argument, process each one in sequence, skip failures, and print a summary at the end. The single-URL interactive mode is preserved unchanged.

---

## Architecture

### New function: `process_one(url, output_dir) -> bool`

Extracts the single-URL pipeline from `main()`. Handles one URL end-to-end:
1. Fetch video info
2. Download audio to temp dir
3. Transcribe
4. Write `.md` file to `output_dir`
5. Clean up temp files
6. Return `True` on success, `False` on any failure (printing the error, not raising)

Returns a `bool` so the batch loop can count successes/failures without `sys.exit()` terminating the whole run.

### Updated `main()`

Checks `sys.argv`:
- **No argument:** existing interactive prompt → calls `process_one()` once, `sys.exit(1)` on failure (preserving current behavior)
- **One argument:** treated as a path to a URLs file → batch mode

### Batch mode logic in `main()`

1. Read the file; strip blank lines and lines starting with `#`
2. Print `"YouTube Video Transcriber — Batch Mode (N URLs)"`
3. Loop with `[i/N]` prefix per URL, calling `process_one()`
4. After all URLs, print `"Done: X succeeded, Y failed."`

---

## `urls.txt` File Format

```
# Optional comments ignored
https://youtube.com/watch?v=...
https://youtube.com/watch?v=...

https://youtube.com/watch?v=...
```

- Blank lines ignored
- Lines starting with `#` ignored
- One URL per line

---

## User Flow

```
$ python transcribe.py urls.txt

YouTube Video Transcriber — Batch Mode (3 URLs)

[1/3] "How to Build a Rocket" by NASA (12:34)
      Downloading... ✓  Transcribing... ✓  Saved: How-to-Build-a-Rocket.md

[2/3] Error: Could not fetch video info for https://youtube.com/bad-url
      Skipping.

[3/3] "Python Tutorial" by Tech Channel (45:02)
      Downloading... ✓  Transcribing... ✓  Saved: Python-Tutorial.md

Done: 2 succeeded, 1 failed.
```

Single-URL mode is unchanged:
```
$ python transcribe.py

YouTube Video Transcriber
Enter YouTube URL: ...
```

---

## Error Handling

- **File not found:** print clear error and `sys.exit(1)` before starting any processing
- **Empty file / no valid URLs after filtering:** print `"No URLs found in file."` and exit cleanly
- **Per-URL failure:** print error with the URL, print `"Skipping."`, increment failure count, continue

---

## Files Modified

| File | Change |
|---|---|
| `transcribe.py` | Extract `process_one()`, update `main()` |
| `tests/test_transcribe.py` | Add tests for `process_one()` and batch parsing logic |

---

## Verification

1. Create a `urls.txt` with 2-3 real URLs and one invalid URL
2. Run `python transcribe.py urls.txt` — confirm valid videos transcribe, invalid URL skips with error, summary counts are correct
3. Run `python transcribe.py` (no args) — confirm single-URL mode still works identically
4. Run `python transcribe.py missing.txt` — confirm clean error message
5. Run `pytest tests/ -v` — all tests pass
