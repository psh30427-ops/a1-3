# AI 상담 운영·확장 설계 — 평가 #16·#17·#18

작성·코드 대조: 2026-11-23. 아래 표에서 **현재 구현**과 **제안 설계(미구현)**를 구분합니다. 설계를 실제 배포 기능이라고 주장하지 않습니다.

## #16 지연 시 대응과 비용·속도 개선

### 현재 구현된 설정

| 위치 | 현재 값 | 사용자에게 미치는 영향 |
|---|---|---|
| backend/coach.py / candidates | 등록 덱 중 최대 4개 후보 | 전체 목록을 매번 모델에 보내지 않음 |
| validate_input / api/recommend.py | 질문 800자, 보유 카드 500자, 본문 8192바이트 | 무제한 입력 방지. 글자 수와 토큰 수는 다름 |
| provider_call / generationConfig | maxOutputTokens=4096 | 출력 길이 상한. 실제 사용 토큰·추론 토큰은 모델 응답 기준 |
| urllib.request.urlopen | timeout=25초 | 제공자 통신 지연 시 504 안내. 함수 전체 실행시간의 엄밀한 상한은 아님 |
| public/js/app.js | AbortController 35초 | 브라우저 대기 중단과 재시도 버튼 복구. 제공자 생성·비용 취소를 보장하지 않음 |
| vercel.json | maxDuration=60초 | 플랫폼 함수 실행 상한 설정 |
| 프론트 busy / 프로세스별 check_rate | 중복 클릭 차단, 분당 5회 | 인스턴스 간 전역 한도는 아님 |

실패 시 메시지와 캡처는 README의 평가 #5 표에 있습니다. 자동 재시도는 현재 하지 않습니다. 429가 난 상태에서 즉시 반복 호출하지 않습니다.

### 단계별 개선 옵션 — 모두 제안 설계

1. **측정부터 적용:** monotonic clock으로 후보 선택/제공자/전체 경과 시간을 분리. 서버 로그에는 requestId, status, model, catalogVersion, durationMs, usage의 토큰 수만 기록합니다. 질문·보유 카드·키·원본 응답은 기록하지 않습니다. 100회 표본의 p50/p95, 실패율, 요청당 토큰을 비교합니다. p95 15초 초과 또는 504 비율 5% 초과를 조정 검토 기준으로 삼습니다. 측정값은 아직 없습니다.
2. **빠른 모드:** 후보 4→2, maxOutputTokens 4096→2048, 모델에 보내는 카드 필드를 id/name/quantity 중심으로 압축. 카드 전체 목록과 출처는 현재처럼 서버가 붙입니다. 신규 env 이름을 FAST_MODE=true, AI_MAX_CANDIDATES=2, AI_MAX_OUTPUT_TOKENS=2048로 제안하지만 **현재 코드는 읽지 않으므로 설정만 넣어도 작동하지 않습니다.** 향후 1~4/512~4096 범위 검증 후 연결합니다. 동일 질문 20개로 JSON 완료율·추천 근거·기존 버전 대비 토큰을 검증하고 잘림이 증가하면 원복합니다.
3. **짧은 답변:** playSteps/cautions 각 최대 4개를 3개로 제한하는 schema v2를 별도 버전으로 도입. 표본 검증 없이 출력 상한만 낮춰 잘린 JSON을 성공처럼 표시하지 않습니다.

### 캐싱 전략 — 제안 설계

- 정적 catalog는 별도 공개 자료이며 사용자 상담 결과와 분리합니다. catalog.version이 바뀌면 상담 캐시를 무효화합니다.
- 키: HMAC-SHA256(서버 전용 CACHE_KEY_SECRET, canonical JSON). 정규화된 question/ownedCards/type/style + 후보 ID + catalogVersion + promptVersion + schemaVersion + provider/model을 포함합니다. 임의 구두점 제거로 다른 질문을 합치지 않습니다.
- 동일 요청 성공 결과만 10분 보관. 오류/거절/미검증 JSON은 저장하지 않습니다. 동일 키의 동시 요청은 single-flight로 합칩니다.
- 원문 입력은 저장하지 않고 HMAC 키·검증된 결과만 저장합니다. 결과에도 개인정보가 있을 수 있으므로 개인정보 입력 금지 안내를 유지하고 캐시를 사용자/세션별로 격리합니다. 세션 식별이 없는 현재 서비스에서는 상담 응답 공유 캐시를 활성화하지 않습니다.
- Vercel 서버리스의 Python dict는 여러 인스턴스에 공유되지 않고 재시작 시 사라집니다. 실사용 캐시는 TTL과 접근 통제가 있는 외부 KV가 필요합니다. 무료 과제 버전은 외부 저장소를 추가하지 않았습니다. 현재 API의 Cache-Control: no-store를 유지하며 브라우저/CDN에 상담을 공개 캐시하지 않습니다.
- 성공 기준: 같은 입력 2회에서 제공자 호출 1회, TTL 만료/버전 변경 시 재호출, 다른 사용자·다른 보유 카드 간 결과 혼합 없음.

### 비동기 폴링 — 제안 설계

| 요청 | 응답 | 상태와 정책 |
|---|---|---|
| POST /api/jobs | 202 {jobId,status:"queued",pollAfterMs:2000} | 입력 검증 후 영속 큐 등록. 세션 소유권·Idempotency-Key 검사 |
| GET /api/jobs/{jobId} | 200 {status:"queued" 또는 "running"} | 권장 간격 2초→4초→최대 8초,무작위 지연(jitter) 적용 |
| 같은 GET | 200 {status:"succeeded",result:기존상담응답} | 검증된 응답만 표시 |
| 같은 GET | 200 {status:"failed",error:{code,message}} | 키를 제외한 오류와 수동 재시도 안내 |
| 존재하지 않거나 다른 세션 | 404 | 작업·개인정보 존재 여부 노출 방지 |



- 브라우저는 총 60초 후 폴링을 중단하고 재시도 선택을 제공합니다. 워커는 작업 시작 후 25초 제공자 통신 제한, 전체 작업 만료 2분, 결과 TTL 10분으로 설계합니다.
- 워커의 중복 실행에 대비해 동일 jobId의 완료 저장은 조건부 쓰기. transient 503만 최대 1회 지연 재시도, 인증·요청 오류·한도 초과는 재시도하지 않습니다.
- 큐·작업 상태·세션 검증 저장소를 먼저 확보해야 합니다. HTTP 응답 후 Python thread를 띄워 서버리스가 계속 실행된다고 가정하지 않습니다. 현재 동기 POST /api/recommend를 유지하고, 비동기 기능은 미구현입니다.

## #17 AI 기능 확장과 모듈 경계

### 현재 실제 구조

| 모듈 | 책임 | 금지할 결합 |
|---|---|---|
| public/index.html, css | 폼·메뉴·반응형·접근성 | API 키 포함 금지 |
| public/js/app.js | 검증·fetch·로딩·텍스트 렌더링·로컬 즐겨찾기 | 제공자 API 직접 호출 금지 |
| api/recommend.py | HTTP, Origin 검사, 본문 제한, 임시 rate limit, 오류 JSON | 카드 효과 생성 금지 |
| backend/coach.py | 입력 검증, candidates, schema, Gemini 호출, validate_output | 클라이언트가 보낸 덱 목록을 근거로 신뢰 금지 |
| backend/catalog.json | 검증된 ID·수량·출처·날짜 | 임의 티어/상성 추가 금지 |

### 안정적으로 유지할 기존 API 인터페이스

POST /api/recommend, Content-Type: application/json

```json
{"question":"입문용 덱 추천","ownedCards":"","type":"전체","style":"balanced","consent":true}
```

성공 200: {mode,model,generatedAt,dataCheckedAt,notice,summary,recommendations:[{deckId,reason,playSteps,cautions,deck}],unknowns}. deck의 카드·출처는 서버가 연결합니다. 실패: 해당 4xx/5xx + {error:{code,message}}. 프론트는 code와 한국어 message만 사용하고 내부 예외·키를 렌더링하지 않습니다. 빈 입력400, 본문413, 인증 설정503, 일반 제공자502, 지연504를 계약 테스트로 고정합니다.

### 제공자 어댑터와 기능 플러그인 — 제안 설계

```text
backend/service.py          상담 오케스트레이션
backend/catalog_repo.py     자료 조회·버전
backend/providers/base.py   generate(context, schema, deadline) -> ProviderResult
backend/providers/gemini.py 현 Gemini 요청·응답 변환
backend/features/recommend.py  추천 context/schema/validator
backend/features/explain.py    단일 덱 운영 설명
backend/cache.py            선택 캐시 인터페이스
public/js/api-client.js     fetch·timeout·오류 공통화
public/js/features/coach.js 상담 폼·결과 렌더링
```

서버 내부 allowlist registry: PROVIDERS={"gemini":GeminiProvider}, FEATURES={"recommend":RecommendFeature,"explain":ExplainFeature}. 서버 환경 설정으로만 선택하고 사용자 입력의 모듈 경로·임의 URL·동적 import는 허용하지 않습니다. 어댑터는 정규화된 ProviderError(code,retryable,status)와 구조화 결과를 반환하고 최종 카드 ID 검증은 service에 남깁니다. 새 제공자를 추가할 때 동의 문구와 개인정보 안내도 함께 변경합니다.

### 확장 로드맵과 완료 기준

1. **모듈 분리:** 외부 API 경로·화면 동작을 유지하며 provider mock 계약 테스트 18개 및 브라우저 회귀 테스트 통과.
2. **속도 옵션/관측:** 토큰 설정 검증과 비식별 지연 측정 도입. 동일 20질문 품질표를 비교하고 임의 승률 주장 0건 확인.
3. **운영 설명 기능:** POST /api/v2/explain {deckId,question,consent}. 존재하지 않는 ID404, 미동의400, 서버 자료만 참조. v1 추천은 유지.
4. **캐시/비동기:** 사용자 격리·TTL·전역 제한·영속 큐 확보 후 위 설계 적용. 권한 없는 작업 조회404, 중복 요청에서 중복 호출 방지 테스트.

일정은 기간 약속이 아니라 의존 순서입니다. 신규 자체 덱 생성·실전 시뮬레이터는 검증 가능한 게임 규칙 엔진과 평가 표본을 확보하기 전까지 범위 밖입니다.

## #18 API 키 유출 대응 운영 매뉴얼

대상: Vercel의 GEMINI_API_KEY 및 로컬 .env.local. 책임자: 프로젝트 소유자. 사건이 발생했다는 뜻이 아니라 유출 의심 시 실행할 절차입니다.

1. **즉시 폐기:** 채팅·공개 저장소·스크린샷에 키가 노출되거나 비정상 사용이 감지되면 유출된 것으로 취급합니다. Google AI Studio의 API Keys에서 해당 프로젝트·키를 식별해 키를 삭제/폐기합니다. 화면에서 지우거나 Git 커밋을 되돌리는 것만으로는 충분하지 않습니다. 실제 폐기는 소유자가 실행합니다.
2. **기능 차단:** Vercel 프로젝트 Settings → Environment Variables에서 AI_ENABLED=false로 저장하고 새로 배포합니다. 이는 앱 경로 차단이며 탈취된 키의 외부 직접 사용은 막지 못하므로 1번이 우선입니다. 정적 덱 탐색은 유지합니다.
3. **증거·영향 조사:** 유출 추정 시각~폐기 시각(시간대 포함), 키 이름/리소스 ID, 프로젝트 ID, 저장소·파일·커밋 URL을 기록합니다. 키 원문은 사건 문서에도 복사하지 않습니다. AI Studio Usage/한도, 가능한 결제 기록·프로젝트 로그, Vercel 함수 로그, GitHub secret-scanning 경고와 공개 커밋·PR·Actions 로그·첨부 파일을 조사합니다. 정상 요청과 사용량 급증 시점을 비교합니다. 현재 앱은 상담 원문 로그와 전역 사용자 추적을 수집하지 않아 사용자 단위 영향은 확정 못할 수 있습니다. 로그가 없으면 '없음'이 아닌 '미확인'으로 기록합니다.
4. **새 키 발급·제한:** 같은 키를 재사용하지 않습니다. 필요한 프로젝트/서비스 범위만 갖는 새 키를 만들고 지원되는 API 제한·사용량 제한을 검토합니다. 관련 권한과 연결된 서비스 계정까지 유출됐는지 확인합니다. API 제한만으로 무단 사용이 모두 방지된다고 가정하지 않습니다.
5. **안전하게 교체:** 새 키를 Vercel Production 및 사용하는 Preview 환경에 각각 설정하고 재배포합니다. 로컬은 .env.local에서 교체합니다. 과거 배포가 옛 키를 가지고 있어도 옛 키가 폐기되어 있어야 합니다. 키를 소스·PUBLIC_ 환경 변수·URL·명령 인수·스크린샷에 넣지 않습니다.
6. **노출 흔적 제거:** 공개 파일/이미지/Actions artifact를 정리하고 Git 이력 제거가 필요하면 협업자와 범위를 합의해 별도 수행합니다. 이력 강제 변경을 자동 수행하지 않습니다. 포크·캐시에 복사됐을 수 있으므로 이력 제거는 폐기의 대체가 아닙니다. 사건 시간·커밋 ID 등 비밀이 없는 증거는 보존합니다.
7. **복구 확인:** 소유자가 안전한 환경에서 구 키의 거절 여부와 새 키 상담 1회 성공을 확인하고 AI_ENABLED=true로 복구·재배포합니다. 응답/공개 JS/README에 키가 없고 Git 추적에서도 제외됐는지 점검합니다. 구 키 검사 시 키를 채팅·로그로 출력하지 않습니다. 비정상 이용·비용이 의심되면 제공자 지원에 리소스 ID와 시간 구간으로 문의합니다.
8. **재발 방지:** .gitignore의 .env* 및 .env.example 예외 유지, 커밋 전 secret 검사, 저장소 secret scanning 지원 여부 확인, 로그의 인증 헤더 제거, 개발·운영 키 분리, 협업자 최소 권한, 주기적 사용량 검토. 변경 후 실패 UX와 실제 정상 상담을 다시 확인합니다.

### 사건 기록 양식

발견 시각/시간대, 발견자, 노출 위치, 리소스 ID(키 원문 제외), 폐기 시각, 영향 추정 구간, 확인한 로그와 미확인 범위, 비정상 사용·비용 여부, 새 키 적용 배포 ID, 복구 확인 결과, 재발 방지 담당자와 완료일.

### 공식 참조 · 확인 2026-11-23

- API 키 관리: https://ai.google.dev/gemini-api/docs/api-key
- 프로젝트별 한도 확인: https://ai.google.dev/gemini-api/docs/rate-limits
- Vercel 환경 변수: https://vercel.com/docs/environment-variables

모델별 한도·요금과 콘솔 메뉴는 변경될 수 있으므로 사고 대응 때 실제 프로젝트 화면을 확인합니다.

