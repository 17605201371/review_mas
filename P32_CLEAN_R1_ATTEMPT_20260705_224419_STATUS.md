# P32 Clean Run 1 Attempt Status

Date: 2026-07-05

Status: failed/incomplete run attempt.  Do not count this as a P32 clean
hardneg20 run.

## Run

```text
run_base = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_224419
jsonl = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_224419.jsonl
log = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_224419.log
rows = 16/20
code_commit = e7735c5
code_dirty = clean
max_tokens = 2048
api_max_workers = 4
api_max_retries = 8
api_timeout = 600
DRMAS_JSON_RESPONSE_FORMAT = on
```

## Failure

The run stopped at 16/20 rows because MiMo returned a non-retryable balance
error:

```text
2026-07-05 23:00:08
Error code: 402
message: Insufficient account balance
type: insufficient_balance
```

The pipeline correctly refused to postprocess it:

```text
rows = 16
required = 20
exit = below required min-lines
```

## Completed Rows

```text
ye3NrNrYOY
WNxlJJIEVj
uOrfve3prk
7Dub7UXTXN
9zEBK3E9bX
XyB4VvF01X
GE6iywJtsV
WpXq5n8yLb
NnExMNiTHw
a6SntIisgg
cklg91aPGk
HPuLU6q7xq
fGXyvmWpw6
QAgwFiIY4p
TPAj63ax4Y
mHv6wcBb0z
```

## Operational Notes

- Earlier attempt `20260705_223434` reached 4/20 but was interrupted by the
  tool wait session and is not counted.
- Earlier attempt `20260705_224330` was launched without wait, but the local
  tool environment cleaned up the detached background process before it wrote
  rows; it is not counted.
- The valid recovery action is to restore MiMo balance and rerun a full 20/20
  P32 clean run with the same configuration.
- Do not lower `MAX_TOKENS`, do not count partial16 as clean reproducibility,
  and do not run full39 until P32 has complete clean runs.

