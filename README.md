# 게임 업데이트 반응 분석기

> 게임 패치노트와 유저 리뷰를 연결해, 업데이트 이후 유저 반응이 어떻게 변했는지 분석하고 불만 유형·원인 후보·심각도·운영 대응안을 근거 기반으로 생성하는 RAG/Agent 프로젝트.

---

## 1. 프로젝트 목적

게임 업데이트 이후 유저 반응은 빠르게 변하지만, 운영자가 모든 리뷰를 직접 읽고 패치노트와 연결해 원인을 추정하기는 어렵다. 이 프로젝트는 공개 리뷰와 패치노트를 기반으로 업데이트 전후 반응 변화를 분석하고, 운영자가 확인해야 할 이슈와 대응 초안을 생성하는 것을 목표로 한다.

이 프로젝트는 단순 감성분석이나 리뷰 요약기가 아니다. 핵심은 다음 흐름이다.

```text
업데이트 기준일 설정
→ 패치 전후 리뷰 수집
→ 리뷰 이슈 유형 분류
→ 관련 패치노트/공지 검색
→ 원인 후보와 심각도 생성
→ 운영 리포트와 CS/공지 초안 생성
→ 검색·분류·답변·tool call 로그 저장
→ 평가셋 기반 품질 검증
```

---

## 2. 문제 정의

| 기존 문제 | 프로젝트에서 다루는 방식 |
|---|---|
| 업데이트 이후 부정 반응이 늘었는지 빠르게 파악하기 어렵다 | 패치 전후 기간의 부정 리뷰 비율과 이슈 유형 변화를 비교 |
| 리뷰가 많아 사람이 직접 읽고 분류하기 어렵다 | 리뷰를 버그, 밸런스, 매칭, 성능, 과금, UX 등으로 분류 |
| 어떤 패치 항목과 관련 있어 보이는지 모호하다 | 패치노트/공지 문서를 RAG로 검색해 관련 후보를 연결 |
| LLM이 원인을 단정할 위험이 있다 | “원인 확정”이 아니라 “원인 후보”로 제한하고 근거를 함께 제시 |
| 운영 대응 우선순위가 감에 의존한다 | 리뷰 빈도, 부정도, 심각도, 패치 관련성을 기준으로 우선순위화 |
| 분석 결과를 재현하기 어렵다 | run_id, index_version, prompt_version, eval_dataset_version을 저장 |

---

## 3. 데이터 출처와 현실성 검토

### 3.1 대상 게임

1차 대상 게임은 **이터널 리턴**으로 둔다.

선정 이유:

| 기준 | 판단 |
|---|---|
| 국내 게임 맥락 | Steam 페이지상 개발사는 Nimble Neuron, 퍼블리셔에는 Nimble Neuron, SapStaR Games, KRAFTON, Inc.가 표시됨 |
| 라이브 운영형 게임 | MOBA, PvP, 배틀로얄 성격이라 패치·밸런스·매칭 반응 분석에 적합 |
| 리뷰 수 | Steam 페이지 기준 전체 리뷰와 한국어 리뷰가 충분히 존재함 |
| 패치 반응 분석 가능성 | 캐릭터, 밸런스, 매칭, 성능, 과금, 접속 이슈 등 분류 가능 |

### 3.2 실제 확보 가능한 데이터

| 데이터 | 확보 방식 | 현실성 | 비고 |
|---|---|---:|---|
| 유저 리뷰 | Steam Store Reviews API | 높음 | 공식 문서화된 엔드포인트 사용 |
| 리뷰 메타데이터 | Steam Store Reviews API | 높음 | 작성일, 추천/비추천, 언어, playtime 등 |
| 게임 공지/패치노트 | Steam News API | 중~높음 | `GetNewsForApp` 사용. 단, 모든 뉴스가 패치노트라는 보장은 없음 |
| 패치노트 구조화 | 수집 후 자체 파싱 | 중간 | 제목/본문/날짜 기반 분리 필요 |
| 이슈 유형 라벨 | 직접 라벨링 | 가능 | 최소 500개 리뷰부터 시작 |
| 패치 관련성 라벨 | 직접 라벨링 | 가능하지만 주관성 있음 | true/false/unknown으로 제한 |
| SFT/DPO 데이터 | 직접 구축 | 가능 | 좋은 리포트 vs 위험한 리포트 pair 생성 |

### 3.3 데이터 수집 관련 주의

- Steam Review API와 Steam News API는 공식 문서를 기준으로 사용한다.
- 커뮤니티 게시글, 외부 팬사이트, 비공식 게시판 대량 크롤링은 1차 범위에서 제외한다.
- 리뷰와 패치노트만으로 실제 장애·매칭·밸런스 원인을 확정할 수 없으므로, 결과는 항상 “원인 후보”로 표현한다.
- 내부 게임 운영 지표, 서버 로그, 결제 로그는 접근할 수 없으므로 사용하지 않는다.

---

## 4. 서비스 사용 시나리오

### 시나리오 A. 업데이트 이후 반응 분석

사용자 질문:

```text
최근 업데이트 이후 유저 반응이 나빠졌는지 분석해줘.
```

시스템 결과:

| 항목 | 예시 |
|---|---|
| 분석 기간 | 패치 전 7일 vs 패치 후 7일 |
| 부정 리뷰 비율 변화 | 21% → 38% |
| 주요 이슈 | 매칭 지연, 특정 캐릭터 밸런스, 튕김 |
| 관련 패치 항목 | 매칭 로직 변경, 캐릭터 A 스킬 조정 |
| 판단 방식 | 원인 확정이 아니라 관련 가능성 높은 후보 제시 |
| 운영 우선순위 | 튕김 > 매칭 > 밸런스 |
| 생성 문서 | 운영 리포트, CS 답변 초안, 공지 초안 |

### 시나리오 B. 특정 이슈 확인

사용자 질문:

```text
이번 패치 이후 매칭 관련 불만이 늘었어?
```

Agent 처리:

1. 매칭 관련 리뷰 필터링
2. 패치 전후 매칭 관련 리뷰 비율 비교
3. 패치노트에서 매칭 관련 변경 항목 검색
4. 관련 후보 패치 항목 제시
5. 근거 리뷰와 패치노트 항목 반환
6. 내부 확인이 필요한 지표 제안

### 시나리오 C. 공지/CS 초안 생성

사용자 질문:

```text
접속 오류 관련 유저 공지 초안을 만들어줘.
```

Agent 처리:

1. 접속, 튕김, 크래시 관련 리뷰 검색
2. 관련 공지/패치노트 검색
3. 근거가 부족하면 단정 표현 금지
4. 유저 안내문 초안 생성
5. 실제 게시 전 `approval_required` 상태로 보류

---

## 5. 핵심 기능

| 기능 | 설명 |
|---|---|
| 리뷰 수집 | appid, 언어, 기간, 긍정/부정 기준으로 Steam 리뷰 수집 |
| 패치노트/공지 수집 | Steam News API 기반 공지·뉴스 수집 |
| 리뷰 전처리 | 언어, 작성일, 추천 여부, 텍스트 정제 |
| 패치노트 chunking | 제목, 날짜, 섹션, 패치 항목 단위로 분할 |
| RAG 검색 | 리뷰 이슈와 관련 있는 패치노트/공지 검색 |
| 이슈 분류 | 리뷰를 버그, 밸런스, 매칭, 성능, 과금, UX 등으로 분류 |
| 패치 전후 비교 | 업데이트 전후 기간의 부정 리뷰와 이슈 유형 변화 비교 |
| 운영 리포트 생성 | 주요 이슈, 원인 후보, 근거, 대응 우선순위 생성 |
| CS/공지 초안 생성 | 단정 표현을 피한 유저 안내문 생성 |
| 로그 저장 | request, retrieval, classification, tool call, answer 로그 저장 |
| 평가 | RAG 검색, 이슈 분류, Agent workflow, 위험 답변을 평가 |
| SFT/LoRA | 근거 기반 운영 리포트 스타일을 소형 모델에 튜닝 |
| DPO | 좋은 리포트와 과장된 리포트 pair로 preference tuning 실험 |

---

## 6. RAG/Agent 설계

### 6.1 RAG 역할

RAG는 LLM이 리뷰만 보고 원인을 단정하지 않도록, 패치노트와 공지 문서를 검색해 근거를 제공한다.

| RAG 대상 | 용도 |
|---|---|
| 패치노트 | 캐릭터, 시스템, 밸런스, 매칭, 성능 관련 변경 항목 검색 |
| 공지사항 | 점검, 알려진 이슈, 보상, 안내 사항 확인 |
| 과거 패치노트 | 유사 이슈가 과거에도 있었는지 비교 |

RAG 답변 규칙:

- 답변에는 근거 패치노트/공지 chunk를 포함한다.
- 근거가 없으면 “공개 문서 기준 확인 불가”로 답한다.
- 리뷰는 유저 반응 근거이고, 패치노트는 변경 근거로 분리한다.
- 원인을 확정하지 않고 “관련 가능성” 또는 “운영 확인 필요”로 표현한다.

### 6.2 Agent tool

| Tool | 입력 | 출력 |
|---|---|---|
| `get_reviews_by_period` | appid, start_date, end_date, language | 리뷰 목록 |
| `get_patch_notes` | appid, start_date, end_date | 패치노트/공지 목록 |
| `classify_review_issue` | review_text | issue_type, severity |
| `compare_review_window` | before_reviews, after_reviews | 이슈 변화율 |
| `search_related_patch_notes` | issue_type, query | 관련 patch_note_chunks |
| `rank_issue_priority` | issue_count, severity, trend | 우선순위 |
| `generate_ops_report` | 이슈 요약, 근거 | 운영 리포트 |
| `generate_cs_reply` | 이슈, 근거, 제한사항 | CS 답변 초안 |
| `log_agent_run` | 실행 결과 | 실행 로그 |

### 6.3 Agent 상태값

| 상태 | 의미 |
|---|---|
| `created` | 분석 요청 생성 |
| `reviews_collected` | 리뷰 수집 완료 |
| `patch_notes_indexed` | 패치노트 인덱싱 완료 |
| `classified` | 리뷰 이슈 분류 완료 |
| `retrieved` | 관련 패치노트 검색 완료 |
| `analyzed` | 원인 후보·우선순위 생성 완료 |
| `draft_generated` | 리포트/공지 초안 생성 |
| `approval_required` | 외부 발행 전 승인 필요 |
| `completed` | 분석 종료 |
| `failed` | 실패 |

---

## 7. 8단계 구현 계획

| 단계 | 목표 | 구현 내용 |
|---:|---|---|
| 1 | 최소 세트 | 리뷰/패치노트 수집, RAG 검색, 기본 Agent workflow, 운영 리포트 생성 |
| 2 | 운영성 보강 | 수집 run_id, document hash, index_version, 증분 인덱싱, 롤백 |
| 3 | 관측성 | request/retrieval/classification/tool/latency/token/failure 로그 |
| 4 | 보안/권한 | PII 마스킹, 욕설 원문 노출 제한, prompt injection 방어, 공지 발행 승인 |
| 5 | 테스트/CI | unit/integration/no-answer/prompt-injection/regression test, GitHub Actions |
| 6 | 버전 관리 | prompt/model/embedding/index/eval_dataset/tool_schema version 추적 |
| 7 | SFT/LoRA | 운영 리포트 형식, 단정 금지, 근거 기반 답변 스타일 튜닝 |
| 8 | DPO | 좋은 리포트 vs 과장·단정 리포트 pair로 preference tuning |

---

## 8. 데이터 모델 초안

### `games`

| 컬럼 | 설명 |
|---|---|
| `game_id` | 내부 게임 ID |
| `steam_appid` | Steam appid |
| `game_name` | 게임명 |
| `developer` | 개발사 |
| `publisher` | 퍼블리셔 |

### `review_collection_runs`

| 컬럼 | 설명 |
|---|---|
| `run_id` | 수집 실행 ID |
| `steam_appid` | 대상 게임 |
| `language` | 수집 언어 |
| `start_date` | 수집 시작일 |
| `end_date` | 수집 종료일 |
| `review_type` | all/positive/negative |
| `num_reviews` | 수집 리뷰 수 |
| `status` | success/failed |
| `error_message` | 실패 사유 |

### `reviews`

| 컬럼 | 설명 |
|---|---|
| `review_id` | Steam recommendationid |
| `steam_appid` | 게임 appid |
| `language` | 언어 |
| `review_text` | 리뷰 본문 |
| `voted_up` | 추천/비추천 |
| `timestamp_created` | 작성일 |
| `playtime_forever` | 총 플레이 시간 |
| `run_id` | 수집 실행 ID |

### `patch_notes`

| 컬럼 | 설명 |
|---|---|
| `patch_id` | 패치/공지 ID |
| `steam_appid` | 게임 appid |
| `title` | 제목 |
| `published_at` | 게시일 |
| `content` | 원문 |
| `source_url` | 출처 |
| `version` | 문서 버전 |
| `ingested_at` | 수집일 |

### `review_labels`

| 컬럼 | 설명 |
|---|---|
| `review_id` | 리뷰 ID |
| `issue_type` | bug/balance/matchmaking/performance/monetization/ux |
| `severity` | high/medium/low |
| `patch_related` | true/false/unknown |
| `gold_patch_chunk_id` | 관련 패치노트 chunk |
| `labeler` | 라벨러 |

---

## 9. 평가 설계

### 9.1 RAG 평가

| 지표 | 설명 |
|---|---|
| `retrieval@k` | 정답 패치노트 chunk가 top-k 안에 있는지 |
| `MRR` | 정답 chunk가 얼마나 앞에 나오는지 |
| `citation_accuracy` | 답변의 근거 chunk가 실제 근거인지 |
| `no_answer_accuracy` | 근거 없을 때 답변을 거절하는지 |

### 9.2 리뷰 분류 평가

| 지표 | 설명 |
|---|---|
| `issue_type_accuracy` | 리뷰 이슈 유형 분류 정확도 |
| `severity_accuracy` | 심각도 분류 정확도 |
| `patch_related_accuracy` | 패치 관련성 판단 정확도 |

### 9.3 Agent 평가

| 지표 | 설명 |
|---|---|
| `tool_call_accuracy` | 올바른 tool을 호출했는지 |
| `workflow_completion_rate` | 전체 분석 workflow 완료율 |
| `unsafe_answer_rate` | 원인 단정, 근거 없는 보상 약속 등 위험 답변 비율 |
| `report_usefulness_score` | 사람이 평가한 운영 리포트 유용성 |

---

## 10. SFT/LoRA와 DPO 계획

### 10.1 SFT/LoRA

학습 목표는 “게임 지식 주입”이 아니라 운영 리포트 답변 스타일 튜닝이다.

| 학습 목표 | 예시 |
|---|---|
| 근거 기반 답변 | 리뷰 수치와 패치노트 근거 포함 |
| 단정 금지 | “원인” 대신 “원인 후보” 표현 |
| 운영 액션 제안 | 확인 지표, 담당팀, 우선순위 제안 |
| CS 문안 스타일 | 유저에게 과도한 약속을 하지 않는 안내 |
| 답변 불가 처리 | 근거 부족 시 추가 확인 필요 |

목표 수량:

| 데이터 | 목표 |
|---|---:|
| 운영 리포트 instruction-response | 300~500 |
| CS 답변 초안 | 100~200 |
| no-answer/refusal 케이스 | 100 |
| 근거 기반 답변 | 200 |
| 과장 답변 수정 케이스 | 100 |

### 10.2 DPO

| chosen | rejected |
|---|---|
| “패치 후 7일간 매칭 관련 부정 리뷰가 증가했습니다. 관련 후보는 매칭 로직 변경 항목이며, 원인 확정 전 내부 지표 확인이 필요합니다.” | “이번 패치 때문에 매칭이 망가졌습니다.” |
| “접속 오류 관련 리뷰가 늘었으나 패치노트에 직접 근거는 없습니다. 클라이언트 로그 확인이 필요합니다.” | “패치 이후 접속 오류가 발생한 것이 확실합니다.” |
| “유저 공지 초안: 일부 환경에서 문제가 보고되어 확인 중입니다.” | “문제가 해결될 예정입니다.” |
| “근거 리뷰 12건과 패치노트 항목 2개를 기준으로 원인 후보를 제시합니다.” | “대부분 유저가 이 패치를 싫어합니다.” |

목표 수량:

| 데이터 | 목표 |
|---|---:|
| preference pair | 200~500 |
| 과장 원인 단정 pair | 100 |
| 근거 없는 답변 pair | 100 |
| CS 문안 pair | 100 |

---

## 11. 기술 스택

| 영역 | 선택 |
|---|---|
| 언어 | Python |
| API | FastAPI |
| UI | Streamlit |
| DB | PostgreSQL |
| Vector DB | pgvector 또는 Chroma |
| 배치/수집 | Python scheduler 또는 Airflow Lite 구성 |
| Agent workflow | LangGraph 또는 직접 state machine |
| Embedding | OpenAI embedding 또는 bge 계열 |
| LLM | OpenAI/Claude API, 이후 오픈소스 모델 실험 |
| 튜닝 | Hugging Face Transformers, PEFT, TRL |
| 테스트 | pytest |
| CI | GitHub Actions |
| 배포 | Docker Compose |

---

## 12. 산출물

| 산출물 | 내용 |
|---|---|
| README | 문제 정의, 아키텍처, 실행 방법 |
| 데이터 수집 문서 | Steam API 사용 방식, 수집 범위, 제한 |
| 데이터 카드 | 리뷰/패치노트 데이터 설명과 한계 |
| 라벨링 가이드 | issue_type, severity, patch_related 기준 |
| 평가 리포트 | RAG, 분류, Agent 평가 결과 |
| 운영 리포트 샘플 | 실제 분석 결과 예시 3~5개 |
| SFT/DPO 리포트 | before/after 결과와 한계 |
| Runbook | 수집 실패, 인덱싱 실패, 평가 재실행 방법 |
| 데모 영상 | 3~5분 |

---

## 13. 현실성 검토

### 가능한 것

| 항목 | 판단 |
|---|---|
| Steam 리뷰 수집 | 가능. 공식 Review API 사용 |
| Steam 뉴스/공지 수집 | 가능. 공식 News API 사용 |
| 한국어 리뷰 기반 분석 | 가능. 언어 파라미터와 Steam 페이지의 한국어 리뷰 존재 확인 |
| 패치 전후 비교 | 가능. 패치 날짜 기준 기간 설정 |
| 리뷰 이슈 라벨링 | 가능. 직접 라벨링 필요 |
| 운영 리포트 생성 | 가능. 단, 내부 로그 없이 원인 후보 수준 |
| RAG/Agent 8단계 구현 | 가능. 일부는 PoC 수준으로 명시해야 함 |

### 제한되는 것

| 항목 | 제한 |
|---|---|
| 실제 원인 확정 | 불가. 내부 로그와 실험 데이터 없음 |
| 실제 게임 운영 개선 | 불가. 개인 프로젝트 |
| 실제 공지 발행 | 불가. mock approval로 제한 |
| 커뮤니티 전체 반응 수집 | 1차 범위에서 제외 |
| 대규모 LLM 운영 | 개인 프로젝트 범위 밖 |
| SFT/DPO 실무 경험 주장 | 불가. 개인 실험으로만 표현 |

---

## 14. 포트폴리오용 요약 문장

> 게임 업데이트 이후 유저 리뷰 변화를 분석하는 RAG/Agent 시스템을 구현했습니다. Steam Review API와 Steam News API를 활용해 리뷰와 패치노트 데이터를 수집하고, 패치 전후 리뷰를 이슈 유형별로 분류한 뒤 관련 패치노트 근거를 검색해 원인 후보와 운영 대응 우선순위를 생성했습니다. 또한 요청·검색·분류·tool call·latency·token 사용량 로그를 저장하고, 근거 없는 원인 단정과 과장된 운영 리포트를 평가셋과 DPO 실험으로 개선했습니다.

---

## 15. 말하지 않을 것

| 금지 표현 | 이유 |
|---|---|
| 게임 운영 데이터를 분석했다 | 내부 운영 데이터가 없음 |
| 패치 원인을 자동으로 밝혀냈다 | 공개 리뷰만으로 원인 확정 불가 |
| 실제 운영팀이 사용했다 | 개인 프로젝트 |
| 리뷰 폭탄을 해결했다 | 탐지/분석/초안 생성까지만 가능 |
| LLM 운영 경험 | PoC/개인 프로젝트 수준 |
| SFT/DPO 실무 경험 | 실험으로만 표현 |

---

## 16. 참고 출처

- Steam Store Reviews API: https://partner.steamgames.com/doc/store/getreviews
- Steam News API: https://partner.steamgames.com/doc/webapi/ISteamNews
- Eternal Return Steam page: https://store.steampowered.com/app/1049590/Eternal_Return/
