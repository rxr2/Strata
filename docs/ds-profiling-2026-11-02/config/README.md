# Production config before/after the 2026-11-02 deployment

Files:

- `strata-rx.before.json` — `~/llm/strata/strata-rx.json.bak-20261102-143040`, SHA-256 `97a10dbd…`
  (the production config before the tail-skip/q4 changes).
- `strata-rx.after.json` — SHA-256 `66583d89…` (the deployed config).

Only these changed:

| key | before | after |
|---|---|---|
| `env.STRATA_ROUTE_TAIL_SKIP` | absent | `7` |
| `--mtp-draft-vocab` | absent (the shipped 106 299-id subset) | `/home/rxr2/llm/Strata-data/mtp/vocab/draft_vocab_140k.bin` |
| `--mtp-q4` | absent | `head` |

Unchanged: `--pcie-frac 0.20`, `--vram-reserve-mib 3072`, `--spec-min-p 0.85`, `--spec 6`, `--kv int8`,
`--resident-experts --resident-budget-gib 36`, `--pool-workers 7`, `--adapt-*`, the rest.

`strata-rx.after.json` contains the original machine's absolute model paths (`/run/media/...`,
`/home/rxr2/...`); adapt them on another box. The vocabulary file is in `../assets/draft_vocab_140k.bin`
(the config points to the local copy under `~/llm/Strata-data/mtp/vocab/`).

Rollback:

```sh
cp -p strata-rx.before.json ~/llm/strata/strata-rx.json
systemctl --user restart strata-rx
```

The deployed config produced (3 fixed prompts): 96.9 / 112.7 / 87.6 tok/s (mean 99.07; old 94.2);
combined quality KL 0.01747, top-1 29/32 (see `../results/`). The top-1 is one below the 30/32 gate;
the owner accepted the trade when asking for the deployment.

No API keys, tokens or passwords are in these files — only model paths and engine arguments.
