# 먼저 읽어주세요

이 패키지는 `psh20721-ux/tcg-make` 저장소의 Codespaces에 직접 올릴 과제용 웹 서비스입니다.

1. 받은 ZIP을 Codespaces 왼쪽 파일 탐색기의 저장소 최상위에 올립니다.
2. 터미널에서 실행합니다.

```bash
python3 -m zipfile -e pocket-deck-coach-assignment.zip .
python3 scripts/serve.py
```

3. Ports 탭에서 5310번 주소를 열면 사이트를 볼 수 있습니다.

실제 AI 상담을 켜려면 `.env.example`을 `.env.local`로 복사하고, 편집기에서 `GEMINI_API_KEY`를 직접 설정한 다음 서버를 다시 실행하세요. 키는 채팅에 보내지 않습니다. 키가 없을 때도 덱 탐색과 명확히 표시된 결과 예시를 볼 수 있습니다.

이어서 [배포 안내](docs/DEPLOYMENT.md)를 따라 GitHub 커밋·푸시와 Vercel 배포를 진행합니다. 최종 과제 제출에는 실제 배포 URL과 실제 AI 호출 화면을 추가해야 합니다.

- [서비스 기획서](docs/SERVICE_PLAN.md)
- [README](README.md)
- [제출 체크리스트](docs/SUBMISSION_CHECKLIST.md)
- [AI 코딩 도구 사용 과정](evidence/AI_CODING_PROCESS.md)

