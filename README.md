
# ROOM 09 FINAL BOT

바로 실행해서 쓸 수 있게 정리한 완성형 디스코드 봇입니다.

## 이번 최종판 추가점
- `/도움말` 에서 **카테고리별 전체 명령어 표시**
- `/명령어` 에서 **전체 명령어 표를 한 번에 전부 출력**
- 명령어 대부분 **한글 슬래시 명령어**
- 압축 풀고 토큰/서버 ID 넣으면 바로 실행 가능
- 기존 완성형 기능 유지:
  - 환영 / 공지 / 투표 / 경고 / 청소
  - 금지어 / 도배 제한
  - 티켓 / 셀프 역할
  - RPG / 몬스터 / 상점 / 아이템
  - 보스전 / 보스 패턴 / 보스 랭킹
  - 일일보상 / 일일퀘스트
  - 칭호 / 도전과제
  - 관리자 확장 명령어
  - 브랜딩(이름/상태/아이콘)

## 설치
```bash
pip install -r requirements.txt
```

Windows CMD
```cmd
set DISCORD_BOT_TOKEN=여기에_토큰
set GUILD_ID=여기에_서버ID
python bot.py
```

PowerShell
```powershell
$env:DISCORD_BOT_TOKEN="여기에_토큰"
$env:GUILD_ID="여기에_서버ID"
python bot.py
```

## 필수 추천 첫 세팅
```text
/채널설정 kind:welcome channel:#환영
/채널설정 kind:log channel:#로그
/채널설정 kind:announce channel:#공지
/채널설정 kind:ticket_category channel:티켓카테고리
/채널설정 kind:ticket_panel channel:#ticket-panel
/채널설정 kind:image channel:#images
/환영문구 문구:{mention} 들어왔다
/역할패널
/티켓패널
/rpg패널
/보스패널
```

## 명령어 보기
- `/도움말`
- `/도움말 카테고리:기본`
- `/명령어`

## 브랜딩
- `/브랜드설정 이름:ROOM09 상태문구:ROOM 09 가동 중 상태종류:playing 시작시적용:true`
- `/브랜드아이콘경로 경로:assets/icon.png`
- `/브랜드적용`

## 주의
- 봇 이름/아이콘 변경은 디스코드 자체 제한이 있습니다.
- 상태 문구는 바로 바뀌지만, 이름/아이콘은 늦거나 실패할 수 있습니다.
- 이미지 자동생성이 실제로 연결되어 있습니다. `OPENAI_API_KEY`를 설정하면 `/맵이미지`, `/몬스터이미지`, `/보스이미지`가 실제 이미지를 생성합니다.


## 실제 이미지 생성 사용법
환경변수 추가:
```cmd
set OPENAI_API_KEY=여기에_OpenAI_API_키
```

PowerShell:
```powershell
$env:OPENAI_API_KEY="여기에_OpenAI_API_키"
```

그 다음 사용:
- `/맵이미지 설명:폐쇄된 실험실 복도`
- `/몬스터이미지 몬스터코드:slime`
- `/보스이미지 보스코드:alpha`

생성된 이미지는 `image`로 지정한 채널이 있으면 거기에 올라가고,
없으면 명령어를 실행한 채널에 올라갑니다.
