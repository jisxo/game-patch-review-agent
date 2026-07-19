# Review Issue Labeling Guide

## Rules

- Assign every label explicitly supported by the review; multiple labels are allowed.
- Copy exact text into `evidence_spans`.
- Do not infer a patch relationship, root cause, affected population, or operational severity.
- Use `other` only when no defined issue is explicitly present.
- `expression_intensity` describes wording, not real-world incident severity.

## Taxonomy

| Label | Include | Exclude |
|---|---|---|
| `matchmaking` | queue time, team composition, matchmaking quality | network latency |
| `server_connection` | login, disconnection, ping, server access | local frame rate |
| `performance` | FPS, stutter, optimization, resource usage | gameplay balance |
| `bug` | crashes, errors, broken behavior | disliked intentional changes |
| `balance` | buffs, nerfs, overpowered or weak mechanics | purely cosmetic preference |
| `character` | character design, skills, character-specific feedback | general balance with no character context |
| `monetization` | price, paid items, battle pass, purchase policy | free progression UX only |
| `ux` | UI, controls, menus, usability | technical frame rate |
| `other` | meaningful feedback outside the taxonomy | empty or spam text |

## Ambiguous cases

Record difficult cases in the evaluation dataset notes. Run a pilot before freezing the taxonomy.
If only one labeler is available, relabel a subset after a delay and report agreement rather than
presenting the labels as objective truth.

## JSONL format

```json
{"review_id":"123","review":"매칭 대기가 너무 길어요","issue_types":["matchmaking"],"evidence_spans":["매칭 대기가 너무 길어요"],"expression_intensity":"medium"}
```
