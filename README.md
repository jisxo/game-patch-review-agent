# Game Update Reaction Analyzer

> Steam 한국어 리뷰와 게임 패치노트·공지를 이용해 업데이트 전후의 반응 변화를 관측하고, LLM/RAG로 리뷰 이슈와 관련 가능한 공개 근거를 연결하는 분석 시스템

## 1. 프로젝트 정의

라이브 서비스 게임은 업데이트 직후 밸런스, 매칭, 서버, 버그, 성능 등 다양한 반응을 받는다. 하지만 운영자가 많은 리뷰를 직접 읽고, 반응 변화와 패치 내용을 연결해 우선 확인할 문제를 찾는 데는 시간이 걸린다.

이 프로젝트는 Steam 공개 데이터를 이용해 다음 과정을 지원한다.

```text
분석 가능한 패치 탐색
→ 패치 전후 리뷰 수집
→ 통계와 규칙 기반 baseline 생성
→ LLM으로 리뷰 이슈 구조화
→ 관련 패치노트·공지 검색
→ 근거가 연결된 분석 리포트 생성
→ 검색·분류·생성 품질 평가
```

이 시스템의 사용자는 게임 라이브 운영 또는 커뮤니티 담당자를 가정한다. 결과는 실제 원인을 확정하거나 운영 결정을 자동화하는 도구가 아니라, **공개 유저 반응을 빠르게 탐색하고 내부 확인 대상을 좁히는 분석 보조 자료**다.

### 분석 대상

| 항목 | 내용 |
|---|---|
| 대상 게임 | Eternal Return / 이터널 리턴 |
| Steam App ID | `1049590` |
| 분석 대상 | Steam에 작성된 한국어 리뷰 |
| 변경 근거 | Steam News API로 수집한 패치노트·핫픽스·공지 |
| 기본 분석 단위 | 특정 패치 게시 시각 전후의 리뷰 window |

이 프로젝트에서 말하는 유저 반응은 국내 전체 유저의 반응이 아니라 **Steam 한국어 리뷰 작성자의 반응**으로 한정한다.

## 2. 핵심 질문

이 프로젝트는 다음 질문에 답하는 것을 목표로 한다.

1. 특정 업데이트 전후로 리뷰 수와 추천 비율이 어떻게 달라졌는가?
2. 매칭, 서버, 밸런스, 버그 등 어떤 이슈가 증가하거나 감소했는가?
3. 관측된 리뷰 이슈와 관련 가능성이 있는 패치노트 또는 공지는 무엇인가?
4. 각 분석 문장을 어떤 리뷰와 문서 근거로 뒷받침할 수 있는가?
5. 공개 근거가 부족할 때 원인을 단정하지 않고 판단을 보류할 수 있는가?
6. 규칙 기반 방법과 비교했을 때 LLM/RAG가 실제로 무엇을 개선했는가?

## 3. 포트폴리오에서 증명할 역량

### 문제 정의와 현실성 검증

최신 기술을 먼저 적용하지 않고, 실제 확보 가능한 데이터와 사용자의 의사결정 문제를 확인한 뒤 해결 범위를 정한다.

### 재현 가능한 데이터 파이프라인

Steam API 수집, 응답 검증, 중복 방지, 수집 이력, 분석 설정과 결과 버전을 저장해 동일한 분석을 다시 실행할 수 있게 한다.

### 관측과 추정의 분리

| 구분 | 의미 | 예시 |
|---|---|---|
| `observed` | 데이터에서 직접 계산하거나 확인한 사실 | 패치 후 매칭 관련 리뷰 비율 증가 |
| `related_evidence` | 검색된 공개 문서상의 관련 후보 | 같은 기간의 매칭 로직 변경 항목 |
| `needs_verification` | 공개 데이터로 확인할 수 없는 사항 | 실제 서버 장애 여부와 내부 원인 |

리뷰 변화와 패치 항목이 함께 발견되어도 인과관계로 단정하지 않는다.

### 평가 가능한 LLM/RAG

LLM은 Steam에 이미 존재하는 `voted_up` 값을 다시 감성 분류하는 데 사용하지 않는다. 리뷰 이슈 구조화, 관련 문서 검색, 근거 기반 리포트 생성에 사용하며 규칙 기반 baseline과 비교한다.

### 서비스 엔지니어링

모델 호출뿐 아니라 API, DB, 테스트, CI, 오류 처리, latency·token·cost 측정, 입력 안전성까지 포함한 end-to-end 시스템을 구성한다.

## 4. 데이터 출처와 제약

| 데이터 | 출처 | 사용 목적 | 주요 제약 |
|---|---|---|---|
| 한국어 리뷰 | Steam Store Reviews API | 리뷰 수, 추천 비율, 이슈 변화 | 전체 플레이어를 대표하지 않음 |
| 리뷰 메타데이터 | Steam Store Reviews API | 작성·수정 시각, 추천 여부, 플레이 시간 | 리뷰가 사후 수정될 수 있음 |
| 뉴스·공지 | Steam News API | 패치 후보와 공개 근거 | 모든 뉴스가 패치노트는 아님 |
| 패치 본문 | Steam News API `contents` | 정제, chunking, 검색 | 마크업 정제와 구조 복원이 필요함 |

리포트에는 다음 제약을 항상 표시한다.

- Steam 한국어 리뷰만 사용한다.
- 리뷰 작성자는 전체 플레이어의 무작위 표본이 아니다.
- 뉴스 게시 시각과 실제 패치 적용 시각이 다를 수 있다.
- 분석 구간에 다른 패치나 핫픽스가 포함될 수 있다.
- 공개 리뷰와 공지만으로 실제 장애나 밸런스 문제의 원인을 확정할 수 없다.
- 리뷰 수가 적은 구간의 비율 변화는 불확실성이 크다.

## 5. 데이터 가능성 검증

### 5.1 선행 검증

최신 패치를 분석 대상으로 고정하지 않는다. 먼저 리뷰 cursor를 순회해 실제 날짜 분포와 수량을 확인하고, 패치 후보별 coverage를 계산한다.

초기 탐색에서는 최신 한국어 리뷰가 `2026-05-06` 부근으로 확인됐지만, 이 결과는 다음 조건을 검증하기 전까지 최종 데이터 제약으로 확정하지 않는다.

- `filter=recent`
- `language=koreana`
- `purchase_type=all`
- cursor URL encoding과 반복·종료 조건
- Steam이 기본 제외하는 off-topic activity 포함 여부
- `timestamp_created`와 `timestamp_updated`의 구분

off-topic 리뷰는 업데이트 반응에 포함될 수 있으므로, 기본 제외 결과와 포함 결과를 sensitivity analysis로 비교한다.

### 5.2 패치 기준 시각

1.0에서는 Steam News API의 게시 시각을 일관된 분석 기준으로 사용한다.

| 필드 | 의미 |
|---|---|
| `published_at` | Steam News API 뉴스 게시 시각 |
| `analysis_reference_at` | 전후 분석에 사용한 기준 시각 |
| `reference_time_source` | `steam_news_date` |

이는 실제 패치 적용 시각이 아니라 공개 API에서 반복적으로 얻을 수 있는 대체 기준이다.

### 5.3 분석 구간

기본 분석 구간은 전후 7일이다.

```text
before = [analysis_reference_at - 7 days, analysis_reference_at)
after  = [analysis_reference_at, analysis_reference_at + 7 days)
```

DB 계산은 UTC를 기준으로 하고, 사용자 화면에는 UTC와 KST를 구분해 표시한다. 리뷰가 부족하면 window를 임의로 늘리지 않고 coverage 결과와 부적격 사유를 기록한다.

### 5.4 패치 선택 규칙

결과를 본 뒤 변화가 큰 패치를 고르는 체리피킹을 막기 위해 선택 규칙을 분석 전에 고정한다.

1. `patch_note`, `hotfix` 유형만 후보로 사용한다.
2. 후보별 before/after 리뷰 수와 중첩 패치를 계산한다.
3. 양쪽 모두 `min_reviews_per_window`를 충족한 후보만 적격으로 본다.
4. 적격 후보 중 가장 최근 패치를 기본 분석 대상으로 선택한다.
5. 추천 비율이나 이슈 변화는 패치 선택 기준으로 사용하지 않는다.
6. `min_reviews_per_window`는 coverage pilot 이후 결정하고, 결과 분석 전에 버전과 함께 고정한다.

```text
patch_gid | reference_at | window_days | before_count | after_count
          | overlapping_patches | eligible | exclusion_reason
```

### 5.5 프로젝트 진행 조건

다음 조건을 만족해야 LLM/RAG 단계로 진행한다.

- 전후 비교가 가능한 역사적 패치가 최소 3개 이상 존재한다.
- 리뷰에 분류 가능한 이슈 정보가 충분히 포함되어 있다.
- 여러 시기의 패치노트·공지로 검색 corpus를 구성할 수 있다.
- 수작업 평가셋을 만들 수 있을 정도로 리뷰와 문서의 관계가 해석 가능하다.

조건을 충족하지 못하면 게임, 언어 범위 또는 분석 window 변경을 검토하고 그 결정 근거를 남긴다.

## 6. 시스템 구조

```text
[Steam News API]                 [Steam Review API]
        │                                │
        ▼                                ▼
   news collector                  review collector
        │                                │
        └──────────────┬─────────────────┘
                       ▼
                PostgreSQL storage
          raw data + collection run history
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
 deterministic analysis       document processing
 count / ratio / baseline      clean / chunk / index
          │                         │
          └────────────┬────────────┘
                       ▼
               LLM issue extraction
                       │
                       ▼
        BM25 / dense / hybrid retrieval
                       │
                       ▼
          evidence-linked grounded report
                       │
                       ▼
          evaluation + versioned run logs
                       │
                       ▼
                FastAPI + demo UI
```

기본 분석 흐름은 deterministic pipeline으로 구현한다. 조건부 분기와 tool 선택이 실제로 필요한 분석 질의가 확인되기 전까지 Agent framework를 도입하지 않는다.

## 7. 포트폴리오 1.0 범위

### 포함

- Steam 뉴스 유형 분류와 패치 후보 수집
- Steam 한국어 리뷰 cursor 수집
- PostgreSQL 저장, upsert, 수집 이력 관리
- 패치별 coverage와 사전 정의된 선택 규칙
- 전후 리뷰 수·추천 비율·퍼센트포인트 변화
- 비율의 신뢰구간과 최소 표본 경고
- 규칙 기반 keyword/issue baseline
- LLM structured output 기반 multi-label 이슈 추출
- 패치 문서 정제, 구조 기반 chunking, 인덱싱
- BM25, dense, hybrid retrieval 비교
- 근거 ID와 판단 보류가 포함된 리포트
- 분류·검색·생성·안전성 평가
- latency, token, cost, schema failure 로그
- FastAPI 분석 API와 최소 데모 UI
- pytest, GitHub Actions, Docker Compose

### 제외

- 영어 리뷰와 국가별 비교
- 디시, 인벤, 루리웹 등 커뮤니티 크롤링
- 접속자 수, 매출, 리텐션, CS, 서버 로그 등 내부 데이터
- 실제 공지 또는 CS 답변 발행
- 공개 데이터만으로 원인을 확정하는 기능
- Kubernetes와 대규모 분산 처리
- 실제 프로덕션 트래픽 운영 경험을 가장하는 구성

### 1.0 이후 검토

- 분석 질의에 따른 조건부 Agent workflow
- 영어 리뷰 확장과 교차 언어 검색
- reranker 또는 query transformation
- 모델 routing과 cache를 통한 비용 최적화
- SFT/LoRA 또는 preference tuning

Agent와 fine-tuning은 사용 자체를 목표로 하지 않는다. 평가에서 반복되는 실패가 확인되고, 일반 파이프라인·프롬프트·검색 개선으로 해결하기 어려울 때만 별도 실험으로 진행한다.

## 8. 핵심 설계

### 8.1 수집과 재현성

- API 호출, 응답 검증, 저장, 분석, 출력을 분리한다.
- `recommendationid`와 `gid`를 기준으로 upsert한다.
- 반복 cursor, 빈 페이지, 중복 리뷰, 비정상 timestamp에 명시적 중단 규칙을 둔다.
- 수집 요청 파라미터, 시작·종료 시각, 건수, 중복 수, 실패 사유를 저장한다.
- 원문과 정제된 본문을 분리하고 document hash를 기록한다.
- prompt, model, embedding, chunking, index, label guide, eval dataset 버전을 추적한다.

### 8.2 기본 통계와 baseline

패치 전후에 다음 항목을 비교한다.

- 전체 리뷰 수
- 추천·비추천 리뷰 수
- 추천 비율과 퍼센트포인트 변화
- 가능한 경우 추천 비율의 Wilson confidence interval
- 이슈별 리뷰 수와 전체 리뷰 대비 비율
- overlapping patch와 데이터 부족 경고

keyword baseline은 단어 출현 횟수보다 해당 이슈를 하나 이상 포함한 리뷰 수와 비율을 계산한다. 동의어 사전과 규칙 버전을 저장한다.

### 8.3 리뷰 이슈 구조화

리뷰 한 건은 여러 이슈를 포함할 수 있으므로 multi-label schema를 사용한다.

```json
{
  "review_id": "...",
  "issue_types": ["matchmaking", "performance"],
  "summary": "...",
  "evidence_spans": ["리뷰 원문에 실제로 존재하는 문장"],
  "expression_intensity": "low | medium | high | unknown",
  "confidence": 0.0
}
```

초기 issue taxonomy는 다음과 같이 시작하고, 라벨링 pilot 후 병합하거나 분리한다.

```text
matchmaking / server_connection / performance / bug
balance / character / monetization / ux / other
```

`expression_intensity`는 실제 장애의 심각도가 아니라 리뷰에 나타난 표현 강도다. 모델은 리뷰에 없는 원인이나 영향을 추론하지 않는다.

### 8.4 패치 문서 처리

- HTML·BBCode 등 마크업을 제거하되 원문을 보존한다.
- 제목, 섹션, 하위 항목 구조를 우선해 chunk를 만든다.
- chunk마다 `gid`, 섹션 경로, 원문 위치, hash를 기록한다.
- 선택된 패치 하나만이 아니라 여러 시기의 패치노트·핫픽스·공지로 corpus를 구성한다.
- 한국어 리뷰와 영문 패치노트 간 표현 차이를 검색 실험에 포함한다.

### 8.5 검색 비교

다음 검색 방식을 동일한 평가셋에서 비교한다.

1. keyword baseline
2. BM25
3. multilingual dense embedding
4. BM25 + dense hybrid

reranker는 hybrid 검색에서도 명확한 오류가 남을 때만 추가한다. 기술 스택을 늘리는 것보다 각 방식이 성공하거나 실패한 이유를 분석하는 것을 우선한다.

### 8.6 근거 기반 리포트

리포트는 다음 세 구역을 명확히 분리한다.

```text
Observed changes
- 직접 계산된 통계와 리뷰 이슈 변화

Related public evidence
- 관련 가능성이 있는 패치노트·공지 chunk

Needs verification
- 내부 로그나 추가 데이터가 필요한 사항
```

주요 분석 문장에는 review ID, 통계 run ID 또는 patch chunk ID를 연결한다. 근거가 충분하지 않으면 `insufficient_evidence`를 반환한다.

리뷰와 뉴스 원문은 신뢰할 수 없는 데이터로 취급한다. 문서 안의 명령문을 시스템 지시로 실행하지 않으며, prompt injection과 비정상 입력을 회귀 테스트에 포함한다.

## 9. 평가 계획

### 9.1 평가셋

개인 프로젝트에서 수작업 품질을 유지할 수 있는 범위로 구성한다.

| 평가 대상 | 목표 규모 | 용도 |
|---|---:|---|
| 리뷰 이슈 라벨 | 150~300개 | baseline과 LLM 이슈 추출 비교 |
| 검색 query·정답 chunk | 50~100개 | retrieval 비교 |
| 근거 기반 리포트 사례 | 30~50개 | claim grounding과 판단 보류 평가 |
| 근거 부족·공격 입력 | 20~30개 | no-answer와 prompt injection 평가 |

라벨링 가이드를 먼저 작성하고 일부 데이터를 pilot labeling한 뒤 taxonomy를 고정한다. 가능하면 두 번째 라벨러의 검토를 받고, 어려우면 일정 간격을 둔 재라벨링으로 일관성을 확인한다.

### 9.2 지표

| 영역 | 핵심 지표 |
|---|---|
| 이슈 추출 | 라벨별 Precision/Recall, Macro-F1, schema failure rate |
| 검색 | Recall@k, MRR 또는 nDCG |
| 생성 | claim-level evidence support, citation precision, unsupported claim rate |
| 판단 보류 | abstention precision/recall, no-answer accuracy |
| 운영성 | latency, token usage, cost per report, retry/failure rate |
| 안전성 | prompt injection 방어율, malformed input 처리율 |

LLM-as-a-judge는 수작업 gold label을 대체하지 않고 보조 지표로만 사용한다. 평가 prompt와 judge model도 버전으로 관리한다.

### 9.3 필수 비교 실험

- keyword baseline vs LLM issue extraction
- BM25 vs dense vs hybrid retrieval
- citation 강제 전후 unsupported claim 비율
- 근거 부족 규칙 적용 전후 no-answer 성능
- off-topic 리뷰 포함 여부에 따른 분석 결과 변화
- chunking 또는 embedding 변경 전후 검색 품질·비용 변화

최종 리포트에는 가장 좋은 결과뿐 아니라 실패 사례와 개선 전후를 함께 공개한다.

## 10. 데이터 모델 초안

| 테이블 | 역할 |
|---|---|
| `games` | 분석 대상 게임 기준 정보 |
| `collection_runs` | 뉴스·리뷰 수집 실행 이력과 요청 파라미터 |
| `steam_news` | 뉴스·공지·패치 후보 원문과 분류 결과 |
| `steam_reviews` | 한국어 리뷰 원문과 메타데이터 |
| `patch_window_reports` | 패치 전후 기본 분석 설정과 결과 |
| `document_chunks` | 정제된 패치·공지 chunk와 위치·hash |
| `review_issue_predictions` | baseline·LLM 이슈 추출 결과와 버전 |
| `retrieval_runs` | query, 검색 방식, 순위, 점수, index version |
| `analysis_runs` | 통계·검색·생성 실행을 연결하는 분석 run |
| `report_claims` | 리포트 문장과 연결된 review·chunk 근거 |
| `eval_examples` | 평가 입력, gold label, dataset version |
| `eval_results` | 모델·검색·생성 평가 결과 |

1차 DB migration에서는 Data MVP에 필요한 테이블만 만들고, LLM/RAG 테이블은 해당 단계에서 추가한다.

## 11. 기술 스택과 선택 기준

| 영역 | 1.0 선택 | 이유 |
|---|---|---|
| 언어 | Python | 데이터·LLM 생태계와 채용 직무 적합성 |
| API | FastAPI | typed schema와 비동기 API 구성 |
| DB | PostgreSQL | 원문·실행 이력·분석 결과 통합 관리 |
| Vector search | pgvector | 별도 Vector DB 운영 없이 PostgreSQL과 통합 |
| Keyword search | BM25 baseline | dense 검색의 효과를 비교할 기준 |
| LLM | API 기반 모델 1종부터 시작 | 평가 기준을 먼저 고정하고 모델 수를 제한 |
| Embedding | 한국어·영어 지원 multilingual 모델 | 교차 언어 검색 대응 |
| UI | Streamlit 또는 최소 웹 UI | 분석 결과와 근거 탐색용 데모 |
| 테스트 | pytest | 수집·분석·평가 회귀 테스트 |
| CI | GitHub Actions | 테스트와 평가 smoke test 자동화 |
| 배포 | Docker Compose | 로컬 재현성과 의존성 격리 |

처음부터 orchestration framework에 의존하지 않는다. 직접 구현한 pipeline으로 책임과 입출력을 명확히 한 뒤, 복잡도가 실제로 증가할 때 LangGraph 같은 도구를 검토한다.

## 12. 개발 로드맵

### Phase 0. Feasibility Gate

완료 조건:

- 한국어 리뷰 날짜·수량 분포 확인
- cursor 종료·중복·off-topic 처리 검증
- 패치 후보별 coverage 표 생성
- 분석 가능한 패치 최소 3개 확인
- 데이터가 부족할 경우 범위 변경 결정 기록

### Phase A. Data MVP

완료 조건:

- 리뷰와 뉴스의 재현 가능한 수집·저장
- 수집 이력, 중복 수, 실패 사유 기록
- 패치 선택 규칙과 window 분석 구현
- 리뷰 수·추천 비율·신뢰구간 생성
- versioned keyword baseline 생성
- CLI 또는 API로 결과 재현

### Phase B. LLM/RAG MVP

완료 조건:

- 패치 문서 정제와 구조 기반 chunking
- structured output 이슈 추출
- BM25·dense·hybrid 검색 구현
- 주요 문장에 근거 ID가 있는 리포트 생성
- 근거 부족 시 `insufficient_evidence` 반환

### Phase C. Evaluation

완료 조건:

- 라벨링 가이드와 versioned 평가셋 공개
- baseline 대비 분류·검색 성능 비교
- unsupported claim과 판단 보류 평가
- latency·token·cost·failure 측정
- prompt injection과 회귀 테스트 구성

### Phase D. Portfolio Delivery

완료 조건:

- FastAPI와 최소 데모 UI
- Docker 기반 재현 가능한 실행 환경
- 테스트와 CI 통과
- 실제 분석 사례 3~5개
- 실패 사례와 개선 전후 평가 리포트
- 3~5분 데모 영상과 면접용 아키텍처 설명

## 13. 데모 시나리오

사용자가 분석 가능한 패치를 선택하면 다음 화면을 제공한다.

1. 패치 기준 시각과 before/after coverage
2. 리뷰 수와 추천 비율 변화
3. 이슈 유형별 리뷰 비율 변화
4. 대표 리뷰와 원문 evidence span
5. 관련 패치노트·공지 chunk와 검색 점수
6. `observed`, `related_evidence`, `needs_verification` 리포트
7. 데이터 부족, 중첩 패치, 근거 부족 경고

챗봇 UI보다 분석 근거와 불확실성을 한 화면에서 검증할 수 있는 대시보드를 우선한다.

## 14. 실행 방법

### 환경 구성

```bash
cp .env.example .env
python -m pip install -r requirements.txt
docker compose up -d
python -m app.cli.migrate
```

`OPENAI_API_KEY`가 없어도 수집, 기본 통계, keyword baseline, BM25 검색, deterministic 리포트를 실행할 수 있다. LLM 이슈 추출, dense/hybrid 검색, LLM 리포트 생성에는 API 키가 필요하다.

### 데이터 수집과 분석

```bash
python -m app.cli.collect_data news --count 100
python -m app.cli.collect_data reviews --max-pages 10
python -m app.cli.show_coverage
python -m app.cli.index_news
python -m app.cli.analyze_patch PATCH_GID --method bm25
```

LLM/RAG 전체 경로는 다음처럼 실행한다.

```bash
python -m app.cli.index_news --with-embeddings
python -m app.cli.analyze_patch PATCH_GID \
  --method hybrid \
  --issue-method llm \
  --generation-method llm
```

### API

```bash
python -m uvicorn app.api.main:app --reload
```

| Endpoint | 역할 |
|---|---|
| `GET /` | 패치 분석 대시보드 |
| `GET /health` | DB 연결 상태 확인 |
| `GET /patches` | 패치 후보 조회 |
| `GET /coverage` | 후보별 전후 리뷰 coverage |
| `POST /index` | 뉴스 문서 chunking·embedding |
| `GET /search` | BM25·dense·hybrid 검색 |
| `POST /reports/{patch_gid}` | 패치 window 분석과 근거 리포트 |

## 15. 현재 구현 상태

### 코드 구현 완료

- PostgreSQL·Docker 기본 구성
- Python DB 연결
- Steam News API 호출
- 뉴스 제목 기반 유형 분류
- `steam_news` 저장·upsert
- patch candidate 조회 CLI
- patch window 계산 초안
- Steam Review API 1페이지 호출과 cursor 확인
- cursor 반복·빈 페이지·retry·off-topic 옵션을 포함한 다중 페이지 수집
- 리뷰 upsert와 수집 run 성공·실패 이력
- 패치별 coverage와 중첩 패치 탐지
- 추천 비율, Wilson confidence interval, 이슈 비율 baseline
- 패치 문서 정제, section chunking, hash와 provenance
- BM25, pgvector dense, reciprocal-rank hybrid 검색
- structured output LLM 이슈 추출과 exact evidence span 검증
- deterministic 또는 LLM 기반 grounded report와 citation allowlist 검증
- 분석·검색·모델·토큰·latency 실행 로그
- FastAPI endpoint와 평가 CLI
- 통계·분류·chunking·검색·평가·리포트 단위 테스트

### 실제 데이터 통합 검증

2026-07-19에 실제 Steam 공개 데이터로 다음 흐름을 검증했다.

- pgvector PostgreSQL migration과 초기 데이터 생성
- Steam 뉴스 100건 수집·upsert
- 한국어 리뷰 10페이지, 1,000건 수집·upsert
- 수집 범위: `2026-02-04`부터 `2026-05-06`까지
- 전후 7일, 최소 30건 조건을 충족하는 패치 후보 3개 확인
- 뉴스 96건을 146개 chunk로 정제·인덱싱
- 적격 hotfix 1건의 통계·keyword baseline·BM25·grounded report 생성
- 미래 공지가 검색되는 시간 누수를 발견하고 분석 window 필터로 수정
- FastAPI의 health, patches, coverage, search, report endpoint 통합 테스트

### 포트폴리오 완성을 위해 남은 작업

- 수작업 평가셋 구축과 baseline·LLM·검색 실험 결과
- 전체 cursor 탐색과 off-topic 포함 여부 sensitivity analysis
- OpenAI API 키를 사용한 LLM issue extraction과 dense/hybrid 검색 검증
- 실제 API 비용, latency, token 수치 수집
- 분석 사례 3~5개와 데모 영상 제작

오프라인 단위 테스트와 PostgreSQL·FastAPI 통합 테스트는 검증했다. LLM 및 embedding 경로는 API 키가 없어 schema·guardrail 수준까지만 검증했으며 성능 수치를 주장하지 않는다.

전체 진행률을 하나의 퍼센트로 표현하지 않고 각 Phase의 완료 조건으로 관리한다.

## 16. 주요 위험과 대응

| 위험 | 대응 |
|---|---|
| 한국어 리뷰 표본 부족 | coverage gate 후 게임·언어·window 변경 여부 결정 |
| 게시 시각과 실제 적용 시각 불일치 | `reference_time_source` 표시, 인과 표현 금지 |
| 중첩 패치와 외부 이벤트 | window 내 다른 변경 사항을 함께 기록 |
| 이슈 taxonomy의 주관성 | pilot labeling과 라벨 가이드, multi-label 허용 |
| 패치 관련성 과대 해석 | 관련 후보와 원인 확정을 분리, 판단 보류 제공 |
| RAG corpus가 너무 작음 | 여러 시기의 패치·핫픽스·공지 포함 |
| LLM 평가의 자기참조 | 수작업 gold label 중심, judge 모델은 보조로 사용 |
| 기술 스택 과잉 | baseline과 실패가 확인된 경우에만 구성 요소 추가 |
| prompt injection | 원문을 비신뢰 데이터로 격리하고 공격 평가셋 운영 |

## 17. 산출물

| 산출물 | 내용 |
|---|---|
| README | 문제 정의, 범위, 아키텍처, 실행·평가 방법 |
| 데이터 카드 | 수집 데이터, 표본 특성, 사용 제한 |
| 라벨링 가이드 | issue taxonomy와 근거 판단 기준 |
| 평가셋 | 리뷰 분류, 검색, 판단 보류 사례 |
| 평가 리포트 | baseline 비교, 실패 사례, 비용·지연시간 |
| 분석 리포트 샘플 | 실제 패치 분석 결과 3~5개 |
| Runbook | 수집·인덱싱·평가 실패 시 재실행 방법 |
| 데모 | 분석 대시보드와 3~5분 영상 |

## 18. 포트폴리오 표현 원칙

### 최종 요약 문장

> Steam 한국어 리뷰와 패치노트 공개 데이터를 수집해 업데이트 전후의 반응 변화를 분석하고, 규칙 기반 baseline과 LLM/RAG를 비교해 근거가 있는 분석만 생성하도록 설계·평가한 프로젝트입니다. 데이터 가능성 검증부터 검색 품질, claim 단위 근거, 판단 보류, 비용과 실패율까지 재현 가능한 파이프라인으로 관리했습니다.

### 사용하지 않을 표현

| 표현 | 이유 |
|---|---|
| 게임 운영 데이터를 분석했다 | 내부 운영 데이터가 없음 |
| 패치 문제의 원인을 자동으로 밝혀냈다 | 공개 데이터만으로 인과관계 확정 불가 |
| 전체 국내 유저 반응을 분석했다 | Steam 한국어 리뷰로 표본이 제한됨 |
| 실제 운영팀이 사용했다 | 개인 프로젝트 |
| 프로덕션에서 대규모 운영했다 | 개인 개발·배포 범위 |
| Agent나 fine-tuning을 완료했다 | 실제 평가와 구현이 끝난 뒤에만 주장 가능 |

## 19. 참고 자료

- [Steam Store Reviews API](https://partner.steamgames.com/doc/store/getreviews)
- [Steam News API](https://partner.steamgames.com/doc/webapi/ISteamNews)
- [Eternal Return Steam page](https://store.steampowered.com/app/1049590/Eternal_Return/)
