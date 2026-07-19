# Evaluation Protocol

## Datasets

- Issue extraction: 150–300 manually labeled reviews
- Retrieval: 50–100 queries with one or more relevant chunk IDs
- Grounded reports: 30–50 claim-level review cases
- Abstention and injection: 20–30 adversarial or insufficient-evidence cases

Dataset contents are not generated merely to meet a target count. They are added after real data
collection and labeled under `doc/labeling_guide.md`.

## Commands

```bash
python -m app.cli.evaluate_issues evaluation/issues-v1.jsonl --method baseline
python -m app.cli.evaluate_issues evaluation/issues-v1.jsonl --method llm
python -m app.cli.evaluate_retrieval evaluation/retrieval-v1.jsonl --method bm25
python -m app.cli.evaluate_retrieval evaluation/retrieval-v1.jsonl --method dense
python -m app.cli.evaluate_retrieval evaluation/retrieval-v1.jsonl --method hybrid
```

## Reporting

Report macro precision, recall and F1 per issue method; Recall@k and MRR per retrieval method;
claim-level citation support and abstention accuracy for reports; and latency, tokens, cost, schema
failures, and attack pass rate as operational metrics. LLM-as-a-judge may be included only as a
secondary metric alongside manually reviewed examples.
