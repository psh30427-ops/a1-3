# Gemini 적용 순서

1. Codespaces 서버를 Ctrl+C로 종료합니다.
2. 저장소 최상위(README.md와 vercel.json이 있는 곳)에 pocket-coach-gemini-update.zip을 업로드합니다.
3. `python3 -m zipfile -e pocket-coach-gemini-update.zip .`을 실행합니다. 기존 .env.local은 ZIP에 없어 덮어쓰지 않습니다.
4. .env.local 내용을 다음으로 바꾸고 실제 키를 편집기에 직접 넣어 저장합니다.

```dotenv
GEMINI_API_KEY=발급받은키
GEMINI_MODEL=gemini-3.5-flash-lite
AI_ENABLED=true
ALLOWED_ORIGIN=
```

5. `python3 scripts/serve.py`로 실행하고 포트 5310을 여세요.
6. 페이지를 새로고침하고 동의 문구가 Google Gemini인지 확인한 뒤 실제 상담을 요청하세요.
7. 연결 준비됨은 키가 입력됐다는 뜻이며 인증 성공을 보장하지 않습니다. 실제 결과까지 확인하세요.

무료 사용: Google AI Studio 프로젝트가 Free Tier인지 확인하고 유료 결제는 연결하지 마세요. 한도와 접근 가능 모델은 AI Studio에서 확인하세요. 자동 유료 전환·다른 제공자로의 자동 대체는 구현하지 않았습니다. 무료 입력·출력은 Google 제품 개선에 사용될 수 있으므로 개인정보를 입력하지 마세요.

Vercel: 환경 변수 GEMINI_API_KEY, GEMINI_MODEL, AI_ENABLED를 설정하고 재배포하세요. OPENAI_API_KEY와 OPENAI_MODEL은 더 이상 읽지 않습니다.

GitHub 저장 전 `git check-ignore .env.local`로 제외 여부를 확인하세요. 실제 키는 채팅·GitHub·스크린샷에 포함하지 마세요.

공식 자료 확인: 2026-11-18
- https://aistudio.google.com/docs/models/gemini-3.5-flash-lite
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/structured-output

