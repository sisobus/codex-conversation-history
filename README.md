# Codex Conversation History Viewer

macOS용 Codex 대화 기록을 탐색할 수 있는 간단한 인터랙티브 CLI입니다.

## 주요 기능
- 모든 Codex 세션을 날짜별로 탐색
- 하루에 여러 세션이 있을 경우 시간순 정렬 및 페이지네이션 지원
- JSONL 세션 파일을 파싱해 사용자/어시스턴트 메시지를 보기 좋게 표시
- 외부 패키지 없이 Python 표준 라이브러리만 사용

## 설치

### Homebrew (권장)
```bash
brew tap sisobus/tap
brew install cohistory
```

### 수동 설치
1. `cohistory.py`를 다운로드합니다.
2. 실행 권한을 부여합니다: `chmod +x cohistory.py`
3. `PATH`에 추가하거나 `python3 cohistory.py`로 직접 실행합니다.

## 사용법
```bash
cohistory
```

### 탐색 단계
1. **날짜 선택**: Codex 세션이 존재하는 날짜 목록에서 선택합니다.
2. **세션 선택**: 선택한 날짜의 세션 목록(시간 기준 내림차순)에서 원하는 항목을 고릅니다.
3. **대화 보기**: 사용자와 어시스턴트 메시지가 색상과 함께 표시됩니다.

### 조작 방법
- `↑/↓`: 위아래 이동
- `PgUp/PgDn`: 페이지 이동 (목록이 길 때)
- `Enter`: 선택
- 목록 상단의 `< Back to Dates`를 선택하면 날짜 목록으로 돌아갑니다.
- `q`: 종료
- `Ctrl+C`: 강제 종료

## 요구 사항
- macOS (Python 3.9 이상 포함)
- Codex 세션이 `~/.codex/sessions/{year}/{month}/{day}/{*.jsonl}` 경로에 존재해야 합니다.

## 라이선스
MIT License

## 작성자
[sisobus](https://github.com/sisobus)
