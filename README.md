# 포켓 덱 코치

출처가 있는 포켓몬 카드 포켓의 실제 덱 목록을 탐색하고, 보유 카드와 플레이 스타일을 입력해 AI에게 등록 덱 상담을 받는 비공식 팬 제작 학습 서비스입니다. 기존 React 프로젝트를 수정하지 않고 **바닐라 JavaScript + Python**으로 독립 제작했습니다.

- 대상 GitHub 저장소: https://github.com/psh20721-ux/tcg-make
- 배포 URL: https://tcg-make.vercel.app/
- AI 상담: https://tcg-make.vercel.app/#coach
- 로컬 주소: http://127.0.0.1:5310/
- 실제 AI 호출 검증: **2026-11-18 사용자 실행 및 데스크톱·모바일 실 응답 스크린샷 확인. 자동화된 배포 환경 전체 검증은 별도.**
- 코드 작성/과제 선별: 2026-11-16 / 게임 자료 확인: 2026-10-30

## 기능

1. 홈: 서비스 소개와 사용 흐름.
2. 덱 탐색: 실제 20장 제출 목록 10종, 덱/카드 검색, 속성 필터, 브라우저 즐겨찾기, 운영·강점·약점·출처·확인일.
3. AI 상담: 질문/보유 카드/선호 속성/플레이 스타일 입력 → Python API → Google Gemini API → 추천 이유·운영 제안·주의점·미확인 항목 출력.
4. 출처 안내: 원본 링크, 자료 범위, 개인정보 처리와 권리 고지.

결과 예시는 실제 AI 호출 없이 보는 고정 샘플입니다. 자동 테스트의 모의 API 응답에도 테스트 표시가 붙습니다. 둘 다 실제 AI 기능 동작 증빙을 대신하지 않습니다.

## 기술과 구조

```text
public/
  index.html              # 화면 구조와 폼, 4개 메뉴
  css/styles.css          # 색상·간격·반응형·다크패턴 없는 상태 표시
  js/app.js               # DOM, 검색/즐겨찾기, fetch, 로딩/오류 처리
  data/catalog.json       # 공개 가능한 최소 게임 자료
  assets/icon.svg         # 자체 제작 벡터 아이콘
api/recommend.py          # Vercel Python BaseHTTPRequestHandler 엔드포인트
backend/coach.py          # 입력 검증, 후보 선택, 실제 AI 호출, 응답 검증
backend/catalog.json      # 서버가 사용하는 동일한 검증 자료
scripts/serve.py          # 같은 API와 public/을 제공하는 localhost 개발 서버
scripts/browser-test.mjs  # 브라우저 검증·스크린샷 (실제 AI 비용 없음)
requirements.txt          # 런타임은 Python 표준 라이브러리만 사용
vercel.json               # 정적 파일 + Python 함수, 보안 헤더
.env.example              # 환경 변수 이름만 제공
```

프론트엔드는 프레임워크·번들러 없이 동작합니다. Python 3.12의 `urllib`, `http.server`, `json` 등을 사용하므로 AI 호출용 SDK 설치가 필요 없습니다. npm 패키지는 브라우저 검증용 Playwright만 사용합니다.

## 로컬 실행 (Windows PowerShell)

이 폴더에서 실행하세요. 기존 프로젝트의 `npm run dev`와는 별개입니다.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env.local
# .env.local을 편집기로 열어 GEMINI_API_KEY 값을 직접 설정
.\.venv\Scripts\python.exe scripts/serve.py
```

의존성이 없으므로 가상 환경 없이 `python scripts/serve.py`로도 실행할 수 있습니다. http://127.0.0.1:5310/ 접속. 종료는 Ctrl+C. 포트 충돌 시 `python scripts/serve.py --port 5312`.

Codespaces에서는 `python3 scripts/serve.py`로 실행하고 Ports 탭에서 5310번의 전달 주소를 엽니다. `.env.local` 파일은 Git 추적 대상이 아닙니다. 일반 `python -m http.server`는 Python API를 실행하지 않으므로 AI 상담용 실행 방법이 아닙니다.

## 환경 변수

| 이름 | 용도 | 필수 |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini 프로젝트 API 키, 서버에서만 읽음 | 실제 AI 상담에 필요 |
| `GEMINI_MODEL` | Gemini JSON 구조화 출력 호환 모델. 기본 `gemini-3.5-flash-lite` | 선택 |
| `AI_ENABLED` | `true`일 때 실제 호출. `false`로 일시 중지 | 기본 true |
| `ALLOWED_ORIGIN` | 선택적으로 정확한 서비스 origin 지정 | 선택 |

로컬에서는 `.env.local`을 개발 서버가 읽습니다. Vercel에서는 프로젝트 Settings → Environment Variables에 설정하고 **재배포**하세요. 키를 JavaScript, HTML, GitHub, 스크린샷, 채팅에 넣지 마세요. Google AI Studio에서 프로젝트가 Free Tier인지 확인하세요. 무료 한도와 모델 접근 권한은 계정별로 다를 수 있습니다. 모델을 바꾸려면 Gemini JSON 구조화 출력 지원 여부를 확인하세요.

## GitHub · Vercel 준비

[배포 안내](docs/DEPLOYMENT.md)를 순서대로 진행합니다. 과제 폴더 **내용을 저장소 최상위**에 두고 GitHub에 올립니다. Vercel에서 이 저장소를 Import하고 Framework `Other`, Output Directory `public`, 별도 Build Command 없이 배포합니다. `api/recommend.py`와 `backend/**`가 함수에 함께 포함되도록 설정했습니다.

GitHub 코드 업로드와 Vercel 배포를 완료했습니다. 사용자가 배포 주소에서 Gemini 상담을 실행했고 실제 데스크톱·모바일 결과 화면을 제공했습니다. 제출 자료 안내는 [제출 안내](docs/SUBMISSION_GUIDE.md)를 참고하세요.

## 테스트

```powershell
python -m unittest discover -s tests -v
npm ci
npm run check
npm run test:browser
```

브라우저 검증에는 Chrome이 필요합니다. Chrome이 없으면 `npx playwright install chromium` 후 PowerShell에서 `$env:PLAYWRIGHT_CHANNEL='chromium'`을 설정해 실행합니다. 테스트 서버는 localhost:5311을 임시 사용합니다. 유료 AI 요청은 하지 않습니다.

실제 AI 점검: 키를 설정해 서버 재시작 → AI 상담 입력 → 전송 동의 → 응답의 추천·20장·출처·미확인 표시 확인. 공개 배포 후 같은 절차를 URL에서 재검증해야 과제 완료입니다. [검증 기록](docs/TEST_REPORT.md)과 [제출 체크리스트](docs/SUBMISSION_CHECKLIST.md)를 참고하세요.

## 데이터 추가

두 `catalog.json`을 동일하게 유지합니다. 각 덱에 고유 ID, 이름/속성/스타일, 20장 카드 식별자·수량, 자체 운영 설명, 직접 출처 URL, 자료 날짜/확인일을 넣으세요. 카드별 최대 2장과 합계 20장을 테스트가 검사합니다. 확인하지 않은 티어는 `null`입니다. 서버가 후보를 검증하므로 모델이 새 카드 수량이나 출처를 만들어 응답하도록 구성하지 않았습니다. 새 자료를 확인하지 않고 확인 날짜만 갱신하지 마세요.

## 공개 운영 범위

- 일반 사용자 입력을 외부 AI에 전송하기 전 동의를 받으며 상담 내용은 애플리케이션에서 별도 저장하지 않습니다. Google Gemini/Vercel 자체 처리·운영 로그 정책은 별개입니다. Gemini 무료 구간에서는 입력과 출력이 Google 제품 개선에 사용될 수 있습니다.
- 서버는 8KB 본문/800자 질문 제한, 25초 제공자 timeout, 응답 ID/자료 검증과 비밀정보를 제외한 오류 메시지를 사용합니다. 브라우저 timeout은 35초입니다.
- 1분 5회 제한은 **프로세스별 임시 제한**입니다. 서버리스 다중 인스턴스에서 전역 사용량·비용을 보장하지 않습니다. 공개 전 Vercel WAF/플랫폼 이용 제한과 API 프로젝트 한도를 설정하고, 필요시 영속적인 요청 제한을 추가하세요. 단순 Origin 검사는 인증 수단이 아닙니다.
- AI는 등록 덱에서 제안하며 현재 티어·실전 승률·최적 수순을 확인하지 않습니다. 출력 내용은 원본과 대조해야 합니다.
- 카드 이미지·로고·기사 원문은 사용하지 않습니다. 공개 자료 출처와 라이선스 범위는 [권리 고지](THIRD_PARTY_NOTICES.md)에 기록했습니다. 권한이 불명확한 자료는 원본 링크로 연결합니다.

## 기획 및 증빙

- [서비스 기획서](docs/SERVICE_PLAN.md)
- [구조와 학습 설명](docs/ARCHITECTURE.md)
- [배포 및 오류 수정 안내](docs/DEPLOYMENT.md)
- [제출 체크리스트](docs/SUBMISSION_CHECKLIST.md)
- [AI 코딩 도구 사용 과정](evidence/AI_CODING_PROCESS.md)
- 스크린샷: `evidence/screenshots/` (파일명과 모의/실제 여부는 체크리스트에 명시)

향후에는 실제 AI 응답 평가, 추가 검증 자료, 확인 가능한 소유 수량 입력, 영속적인 비용/요청 제한을 확장할 수 있습니다.

## 덱 추가 · 2026-11-18

총 10개 중 신규 3개는 GameWith 유형 평가와 Limitless 실제 제출 20장 목록을 각각 표시합니다. 기존 7개의 확인일은 2026-10-30으로 유지합니다. 자체 티어·개별 레시피 성능·상성은 미확인입니다. [추가 근거](docs/DECK_UPDATE_2026-11-18.md).

