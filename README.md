# oc-meter

Measurement instrument for OpenCode sessions. It measures resources and time, and
emits a canonical JSON record. It does not run prompts, does not modify projects,
does not judge whether the work is correct, and does not compute money. The
experiment driver is a separate package.

## What it measures

Internal unit: integer tokens. Rendering in thousands (K) is the responsibility of `report`.

| Quantity | Operational definition | Boundary |
|---|---|---|
| inputTokens | uncached input (`tokens.input`) | assistant messages across the whole tree |
| outputTokens | visible generation (`tokens.output`) | same; excludes reasoning when the provider reports it separately |
| reasoningTokens | reasoning phase (`tokens.reasoning`) | same; double-counting guard |
| cacheReadTokens | tokens served from cache via prefix matching | same |
| cacheWriteTokens | tokens written to cache | same; zero or absent depending on provider → flag |
| wallMs | t0 → t1 with debounce | whole tree, observer's monotonic clock |
| overlapFactor | busySumMs / wallMs | >1 indicates concurrent work |

Derived: promptTokens = input + cacheRead · generation = output + reasoning ·
cacheHitRatio = cacheRead / (cacheRead + input).

Separate `maintenance` bucket for title/summary/compaction. work, maintenance, and
all are reported. Nothing is silently discarded.

## Unit of measurement

Run = root session + all of its descendants.
t0 = submission of the first prompt. t1 = quiescence of the whole tree sustained for δ ms.
δ is declared (default 5000). Both t1Raw and t1Debounced are stored.

## Requirements

- Pinned OpenCode version (export schema and flags drift between versions).
- Disposable container, no credentials. `--auto` turns default `ask` rules
  (including `.env` reads) into allowed ones: there must be no secrets in the environment.
- The provider cache is NOT disabled; it is observed. Alternate arm order across
  replicates so the effect does not accumulate in favor of the same arm.

## Usage
```sh
oc-meter doctor                      # environment cleanliness certificate
oc-meter zero [--live]               # zero measurement (offline by default)
oc-meter measure --root <ses_id> --out record.json
oc-meter report record.json --format markdown|txt
oc-meter compare records/ --group-by arm
```

`report` renders existing records; it never re-measures.

`compare` rejects records with differing model/variant, instrument version,
mappingHash, or workId.

## Calibration

Eight checks (zero, frozen mapping, double counting, tree attribution,
conservation vs stats, clock, determinism, known probe).
`uv run pytest` — the first seven run against fixtures, with no quota consumption.

## Known limitations

- Provider cache: cannot be disabled; order effects between arms.
- Tokenizer: tokens are not comparable across models; model pinned per batch.
- Subagent parallelism: a time gain may come from concurrency rather than
  efficiency; always interpret alongside overlapFactor.