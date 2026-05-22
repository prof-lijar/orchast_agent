# Tiny Jarvis

> [English version](README.en.md) | [상세 튜닝 가이드](docs/guide.ko.md)

**자율 AI 개발팀** — 4명의 AI 에이전트가 실제 소프트웨어 개발팀처럼 협업하여
개인 텔레그램 스케줄링 에이전트를 자율적으로 구축합니다.

## 개요

Tiny Jarvis는 코드를 직접 작성하는 프로젝트가 아닙니다.
AI 에이전트들이 GitHub Issue와 Pull Request를 통해 소통하며
**스스로 제품을 설계하고, 코딩하고, 리뷰하고, 머지**합니다.

```
사용자: python run.py 실행
         ↓
┌─────────────────────────────────────────────┐
│              Orchestrator (run.py)           │
│                                             │
│  ┌─────────┐   매 사이클마다 반복:           │
│  │   PM    │─→ 상태 관찰 → 이슈 생성        │
│  │ Agent   │   → work_plan.json 작성        │
│  └────┬────┘                                │
│       ↓ work_plan.json 기반 실행             │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐   │
│  │Architect │  │ Backend  │  │   QA    │   │
│  │  Agent   │  │  Agent   │  │  Agent  │   │
│  └──────────┘  └──────────┘  └─────────┘   │
│       │              │             │        │
│  PR 머지/설계    코드 구현      PR 리뷰     │
└─────────────────────────────────────────────┘
         ↓
   GitHub Product Repo (결과물)
```

## 에이전트 역할

| 에이전트 | 역할 | 주요 도구 |
|---------|------|----------|
| **PM** | 작업 계획, 이슈 생성, `work_plan.json` 작성 | `create_issue`, `write_file` |
| **Architect** | 시스템 설계, 프로젝트 초기화, 승인된 PR 머지 | `uv_init`, `merge_pull_request` |
| **Backend** | 핵심 코더 — 모든 Python 모듈 구현 | `write_file`, `run_pytest`, `create_pull_request` |
| **QA** | PR 코드 리뷰, 테스트 실행, 승인/반려 라벨링 | `run_pytest`, `run_ruff`, `add_label_to_pr` |

## 구축하는 제품

에이전트들이 만드는 **Tiny Jarvis 제품**:

```
자연어 명령 ("내일 9시에 지수에게 보고서 완성했다고 전해줘")
  → Gemma 로컬 파서 (Ollama)
  → Pydantic 검증된 JSON
  → SQLite 스케줄 저장
  → APScheduler 백그라운드 워커
  → Telethon 텔레그램 메시지 전송
  → 로그 + 상태 업데이트
```

## 빠른 시작

### 1. 사전 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 패키지 관리자
- [Ollama](https://ollama.ai/) + `gemma4:31b` 모델
- [GitHub CLI](https://cli.github.com/) (`gh auth login` 완료)
- 제품 저장소 생성: `gh repo create prof-lijar/mytelegent --public --clone`

### 2. 환경 설정

```bash
cd tiny-jarvis

# .env 파일 생성
cp .env.example .env

# .env 편집 — 아래 값 설정:
# PRODUCT_REPO=prof-lijar/mytelegent
# PRODUCT_REPO_DIR=/절대/경로/tiny-jarvis/product-repo
```

### 3. 의존성 설치

```bash
uv sync
```

### 4. Ollama 모델 준비

```bash
ollama pull gemma4:31b
ollama serve  # 별도 터미널에서 실행
```

### 5. 에이전트 팀 실행

```bash
uv run python run.py
```

에이전트가 자율적으로 사이클을 돌며 제품을 구축합니다.
`Ctrl+C`로 현재 에이전트 턴 종료 후 안전하게 중단합니다 (2번 누르면 강제 종료).

## 프로젝트 구조

```
tiny-jarvis/
├── run.py                  # 오케스트레이션 메인 루프
├── config.py               # 설정 (모델, 리포, 타임아웃)
├── .env                    # 환경 변수 (gitignored)
├── app/
│   ├── agents.py           # 에이전트 정의 + 도구 할당
│   ├── prompts/            # 역할별 시스템 프롬프트 ← 튜닝 포인트
│   │   ├── pm.py
│   │   ├── architect.py
│   │   ├── backend.py
│   │   └── qa.py
│   └── tools/              # 에이전트가 사용하는 도구들
│       ├── files.py        # 파일 읽기/쓰기
│       ├── git.py          # Git 브랜치/커밋/머지
│       ├── github.py       # GitHub 이슈/PR (gh CLI)
│       ├── project_state.py # 프로젝트 상태 스냅샷
│       ├── python_dev.py   # uv, pytest, ruff
│       └── web.py          # 웹 검색/추출
├── product-repo/           # 에이전트가 작업하는 제품 저장소 (클론)
└── pyproject.toml
```

## 튜닝 가이드

에이전트 동작을 커스터마이징하는 방법은 [상세 튜닝 가이드](docs/guide.ko.md)를 참조하세요.

주요 튜닝 포인트:
- **프롬프트 수정**: `app/prompts/*.py` — 에이전트의 행동 지침 변경
- **도구 할당**: `app/agents.py` — 에이전트별 사용 가능 도구 조정
- **모델 변경**: `.env`의 `AGENT_MODEL` — 다른 Ollama 모델 사용
- **에이전트 추가/제거**: `config.py` + `app/agents.py` + `app/prompts/`

## Claude Code / Codex로 작업하기

이 프로젝트는 `CLAUDE.md` 파일에 프로젝트 컨텍스트가 정의되어 있어
Claude Code나 Codex가 즉시 프로젝트를 이해하고 작업할 수 있습니다.

```bash
# Claude Code로 프로젝트 열기
cd tiny-jarvis
claude

# 예시 요청:
# "Backend 에이전트의 프롬프트에 에러 핸들링 가이드라인 추가해줘"
# "새로운 DevOps 에이전트를 추가해줘"
# "run_pytest 도구에 커버리지 옵션 추가해줘"
```

자세한 내용은 [튜닝 가이드](docs/guide.ko.md)를 참조하세요.

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.
