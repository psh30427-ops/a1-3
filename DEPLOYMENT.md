# Codespaces 업로드와 Vercel 배포

대상 저장소: https://github.com/psh20721-ux/tcg-make

현재 파일은 로컬에서 완성한 과제용 패키지입니다. 사용자가 Codespaces에서 직접 업로드하는 방식을 선택했습니다. GitHub 업로드, Vercel 배포, 실제 AI 호출은 각각 아래 절차로 완료하고 증빙을 남깁니다.

## 1. ZIP을 Codespaces에 올리기

1. 받은 `pocket-deck-coach-assignment.zip`을 PC에 저장합니다.
2. `tcg-make` 저장소의 Codespaces를 엽니다. 터미널에서 `git remote get-url origin`을 실행해 대상이 `psh20721-ux/tcg-make`인지 확인합니다.
3. ZIP을 왼쪽 파일 탐색기의 저장소 최상위로 끌어다 놓습니다. `.git` 폴더는 건드리지 않습니다. 기존 파일이 있다면 먼저 변경 사항을 확인하고 필요한 백업을 합니다.
4. Codespaces 터미널에서 실행합니다.

```bash
pwd
git remote get-url origin
python3 -m zipfile -e pocket-deck-coach-assignment.zip .
ls -a
```

최상위에 `public/`, `api/`, `backend/`, `README.md`, `vercel.json`이 보여야 합니다. 중첩된 `assignment-pocket-coach/` 폴더만 보인다면 Vercel Root Directory를 그 폴더로 지정해야 하므로, 이 패키지는 파일들이 바로 최상위에 풀리도록 구성했습니다.

## 2. API 키 설정과 로컬 실행

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env.local
```

편집기로 `.env.local`을 열어 `GEMINI_API_KEY`를 직접 넣으세요. 터미널에 키를 출력하거나 채팅에 붙여 넣지 마세요. 모델 접근 권한과 API 프로젝트 사용 한도를 확인합니다.

```bash
.venv/bin/python scripts/serve.py
```

Ports 탭에서 5310번의 전달 URL을 열어 4개 메뉴와 상담을 확인합니다. `.env.local`은 로컬 개발 전용입니다. Vercel에는 자동으로 전송되지 않습니다. 키가 없으면 실제 상담은 503 안내를 보이고 `결과 예시 보기`만 사용할 수 있습니다.

## 3. 테스트와 GitHub 커밋

새 터미널에서:

```bash
python3 -m unittest discover -s tests -v
npm ci
npm run check
```

브라우저 자동 검증은 Chrome이 필요합니다. Codespaces에서 Chrome이 없으면:

```bash
npx playwright install --with-deps chromium
PLAYWRIGHT_CHANNEL=chromium npm run test:browser
```

브라우저 검증은 5311번 별도 로컬 서버를 사용하고 유료 API 호출을 하지 않습니다. 테스트 스크린샷은 모의 응답이라고 표시돼 있으며 실제 AI 제출 증빙을 대신하지 않습니다.

```bash
git status --short
git add .
git diff --cached --name-only
git commit -m "Build vanilla deck coach with Python AI API"
git push origin main
```

준비된 `.gitignore`가 `.env.local`, `.venv`, `node_modules`, `.vercel`, ZIP 파일을 제외합니다. 커밋 목록에 이 항목이 없는지 반드시 확인합니다. Git 사용자 정보가 없다는 메시지가 나오면 본인의 GitHub 이름·이메일로 저장소의 작성자 정보를 설정한 뒤 커밋하세요. 비밀번호/토큰을 코드나 채팅에 붙이지 않습니다.

## 4. Vercel Import

1. Vercel에 로그인하고 Add New → Project에서 GitHub를 연결합니다.
2. `psh20721-ux/tcg-make`에 접근을 허용하고 Import합니다.
3. 저장소 최상위에 파일을 풀었다면 Root Directory는 기본값으로 둡니다.
4. Framework Preset은 `Other`, Output Directory는 `public`입니다. 별도 빌드 명령은 필요 없습니다. `vercel.json`이 설정을 제공합니다.
5. Environment Variables에 `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash-lite`, `AI_ENABLED=true`를 넣습니다. Production 환경 적용 여부를 확인합니다.
6. Deploy를 누릅니다. 완료된 실제 `https://...vercel.app` 주소를 엽니다.
7. 필요하면 `ALLOWED_ORIGIN`을 그 주소로 설정한 후 재배포합니다. 비워두면 요청 Origin의 host와 요청 Host가 같은지 검사합니다.

일반 정적 호스팅은 Python을 실행하지 않습니다. Vercel의 `/api` Python 파일 기반 함수를 사용해야 합니다. Flask/FastAPI 등을 추가하면 프레임워크 자동 감지가 파일 기반 라우팅보다 우선할 수 있으므로 이 구조와 함께 무심코 설치하지 마세요.

## 5. 배포 후 반드시 확인

- `/`, `/#decks`, `/#coach`, `/#sources` 이동.
- 모바일 화면, 검색·속성·즐겨찾기, 20장 카드 목록.
- 빈 질문과 전송 동의 안내.
- **실제 키로 입력 → Google Gemini → 결과**가 끝까지 이어지는지.
- 결과의 `AI 상담 결과` 표시, 등록된 덱, 출처와 확인 날짜.
- 직접 `/api/recommend`를 GET하면 `ready: true`인지 (키 값은 나오지 않음).
- 실제 AI 동작 장면을 개인정보·키 없이 캡처해 `evidence/screenshots/live-ai.png`로 보관.
- README의 배포 URL과 `docs/SUBMISSION_CHECKLIST.md`의 실제 검증 상태 갱신.

API 호출에는 비용이 발생할 수 있습니다. 앱의 요청 제한은 프로세스별이며 서버리스 전체 비용을 제한하지 않습니다. Vercel WAF/플랫폼 제한과 API 프로젝트 한도를 설정하고 운영 범위에 맞게 점검하세요.

## 6. 오류 수정과 재배포

| 증상 | 확인할 원인과 조치 |
|---|---|
| 페이지 전체 404 | Root Directory/Output Directory가 실제 public 폴더와 맞는지 확인 |
| API가 404 | 정적 서버로만 실행했는지, api/recommend.py가 저장소 최상위 아래 있는지 확인 |
| AI 상담 503·not_configured | Production 환경 변수 입력 후 재배포, 로컬은 서버 재시작 |
| 502·provider_error | API 키·프로젝트 결제/모델 접근·제공자 장애 확인. 키/상세 오류를 화면에 노출하지 않음 |
| 503·provider_busy | 제공자 요청/사용 한도를 확인하고 기다린 뒤 재시도 |
| 504 | 질문을 줄여 재시도. Function 제한 시간·제공자 응답 지연 확인 |
| import/backend 파일 오류 | vercel.json includeFiles의 backend/**와 파일 위치 확인 |
| Origin 403 | ALLOWED_ORIGIN이 실제 https 주소와 정확히 같은지, www/포트/미리보기 도메인 차이 확인 |
| 화면은 성공인데 수량/출처 이상 | AI 응답이 아닌 서버/공개 catalog 두 파일의 내용이 일치하는지 확인 |

원인을 수정한 뒤 테스트 → 커밋 → 푸시 → Vercel 자동 재배포 → 동일 조건 재검증 순서로 진행합니다.

공식 참고: https://vercel.com/docs/functions/runtimes/python/api-directory · https://vercel.com/docs/functions/runtimes/python · https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses

