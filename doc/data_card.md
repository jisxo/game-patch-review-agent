# Data Card

## Dataset

- Source: Steam Store Reviews API and Steam News API
- Game: Eternal Return (`appid=1049590`)
- Review language: `koreana`
- Unit of analysis: review creation timestamp around a Steam news publication timestamp

## Intended use

The data supports a portfolio experiment for issue trend analysis and evidence retrieval. It does
not represent all players and must not be used to assert the root cause of a game incident.

## Collection record

Every collection stores request parameters, run status, row count, failure message, and timestamps.
Reviews use `recommendationid` and news uses `gid` for idempotent upserts. Raw and cleaned document
content are kept logically separate through `steam_news` and `document_chunks`.

## Known limitations

- Review writers are self-selected rather than a random player sample.
- Steam's language value is author-selected.
- Reviews may be edited after creation.
- Off-topic activity is excluded by default by Steam; the project compares excluded and included runs.
- News publication time may differ from the actual deployment time.
- Other patches, hotfixes, events, and external factors may overlap an analysis window.
- No server, revenue, retention, CS, or live-operations data is available.

## Privacy and safety

Steam IDs are not required for analysis and are not stored. Review and news text is untrusted input;
embedded instructions are never executed as system instructions.
