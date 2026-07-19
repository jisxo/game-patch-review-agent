# ERD

## 관계 구조

```text
games
 ├─ collection_runs
 ├─ steam_news ── document_chunks
 ├─ steam_reviews ── review_issue_predictions
 └─ patch_window_reports ── analysis_runs ── retrieval_runs

eval_examples ── eval_results
```

## 테이블 역할

| 테이블 | 기본 키 | 역할 |
|---|---|---|
| `games` | `appid` | 분석 대상 게임 |
| `collection_runs` | `run_id` | API 수집 파라미터, 상태, 건수, 실패 이력 |
| `steam_news` | `gid` | 뉴스·패치·핫픽스 원문과 유형 |
| `steam_reviews` | `recommendationid` | 리뷰 원문과 추천·시간·플레이타임 메타데이터 |
| `patch_window_reports` | `report_id` | 패치 전후 통계, eligibility, keyword baseline |
| `document_chunks` | `chunk_id` | 문서 section, hash, embedding, provenance |
| `review_issue_predictions` | `prediction_id` | baseline·LLM multi-label 이슈 추출 결과 |
| `analysis_runs` | `analysis_run_id` | 모델·프롬프트·인덱스 버전과 최종 리포트 |
| `retrieval_runs` | `retrieval_run_id` | 검색 query, 방법, 순위 결과, latency |
| `eval_examples` | `example_id` | versioned gold 평가 입력과 정답 |
| `eval_results` | `eval_result_id` | 실행 버전별 예측과 평가 지표 |

## 핵심 식별자

- `appid`: Steam 게임 ID
- `gid`: Steam 뉴스 ID이며 패치 분석 기준으로 사용
- `recommendationid`: Steam 리뷰 ID
- `run_id`: 한 번의 수집 실행 ID
- `report_id`: deterministic patch-window 분석 결과 ID
- `analysis_run_id`: 검색·생성 설정을 포함한 한 번의 리포트 실행 ID
- `chunk_id`: 인용 가능한 패치·공지 근거 ID

## 재현성 연결

```text
collection_runs.request_params
  → 수집 원문
  → patch_window_reports(window, rules version)
  → analysis_runs(model, prompt, index version)
  → retrieval_runs(query, method, ranked chunks)
  → report claims(stat ID, chunk ID)
```

`patch_window_reports`는 동일한 패치·window·최소 표본·규칙 버전 조합을 upsert한다.
`analysis_runs`는 같은 통계 결과를 사용하더라도 검색 방식이나 모델이 다르면 별도 실행으로 남긴다.
