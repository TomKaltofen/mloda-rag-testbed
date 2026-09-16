# Scanning this target with llmsectest

```bash
pip install llmsectest
```

Start the app first (see the README quickstart). Every command below assumes `localhost:8000`.

The app echoes `conversation_id` but keeps no history (stateless by design), so a multi-turn probe
degrades to single-turn; that is expected, not a bug.

The pipeline serializes requests behind a single lock (see the README's Architecture section), so
scanning with `codex`/`mistral` should use low or no scanner-side concurrency (omit `--app-stress`,
or pass `--app-stress 1`); concurrent probes queue behind each other's CLI call and can spuriously
time out otherwise.

The system prompt file passed to `--app-prompt` is the packaged one, rendered with the same secret
the app uses; write it to a private temp file once per session:

```bash
SYSTEM_PROMPT_FILE=$(mktemp)
python -c "from mloda_rag_testbed.config import load_settings; from mloda_rag_testbed.corpus.loader import load_system_prompt; s = load_settings(); print(load_system_prompt(s.secret, s.system_prompt_file), end='')" > "$SYSTEM_PROMPT_FILE"
```

## Configuration A: authz on, Bob (canary must NOT be found)

```bash
TESTBED_AUTHZ=on TESTBED_RETRIEVAL=all uvicorn mloda_rag_testbed.app:app --port 8000 &

llmsectest \
  --target app:http://localhost:8000/chat \
  --app-body '{"user": "bob"}' \
  --app-session-field conversation_id \
  --app-secret "SECRET-DEMO-7f2a" \
  --app-canary "CANARY-EXAMPLEBANK-91ac" \
  --app-rag-poison "POISON-EXAMPLEBANK-3b9d" \
  --app-prompt "$SYSTEM_PROMPT_FILE" \
  --preflight \
  --report-formats=sarif,html
```

## Configuration B: authz on, Alice (canary must be found, positive control)

```bash
TESTBED_AUTHZ=on TESTBED_RETRIEVAL=all uvicorn mloda_rag_testbed.app:app --port 8000 &

llmsectest \
  --target app:http://localhost:8000/chat \
  --app-body '{"user": "alice"}' \
  --app-session-field conversation_id \
  --app-secret "SECRET-DEMO-7f2a" \
  --app-canary "CANARY-EXAMPLEBANK-91ac" \
  --app-rag-poison "POISON-EXAMPLEBANK-3b9d" \
  --app-prompt "$SYSTEM_PROMPT_FILE" \
  --preflight \
  --report-formats=sarif,html
```

## Configuration C: authz off (canary must be found, any user)

```bash
TESTBED_AUTHZ=off TESTBED_RETRIEVAL=all uvicorn mloda_rag_testbed.app:app --port 8000 &

llmsectest \
  --target app:http://localhost:8000/chat \
  --app-body '{"user": "bob"}' \
  --app-session-field conversation_id \
  --app-secret "SECRET-DEMO-7f2a" \
  --app-canary "CANARY-EXAMPLEBANK-91ac" \
  --app-rag-poison "POISON-EXAMPLEBANK-3b9d" \
  --app-prompt "$SYSTEM_PROMPT_FILE" \
  --preflight \
  --report-formats=sarif,html
```

## Realistic retrieval

Rerun any configuration with `TESTBED_RETRIEVAL=bm25s` or `TESTBED_RETRIEVAL=graph` to scan the
default, ranked retrieval path instead of the ground-truth pass-through. See the README's
Expected-outcome matrix for what stays deterministic there and what does not.

## Flag-to-env mapping

| llmsectest flag | Env var it must match |
|---|---|
| `--app-secret` | `TESTBED_SECRET` |
| `--app-canary` | `TESTBED_CANARY` |
| `--app-rag-poison` | `TESTBED_POISON` |
| `--app-body '{"user": "..."}'` | selects the authorized document set |
| `--app-prompt` | must be the rendered `TESTBED_SYSTEM_PROMPT_FILE` (or the packaged default) |

If `--app-secret`/`--app-canary`/`--app-rag-poison` do not match the running app's env vars, the
scanner is searching for markers that are not actually planted, and every probe will look
"withstood" for the wrong reason.
