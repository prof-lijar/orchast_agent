# Tiny Jarvis 상세 튜닝 가이드

> [English version](guide.en.md)

이 문서는 Tiny Jarvis 멀티 에이전트 시스템의 작동 원리와
에이전트를 커스터마이징하는 방법을 설명합니다.

---

## 목차

1. [시스템 아키텍처](#1-시스템-아키텍처)
2. [사이클 실행 흐름](#2-사이클-실행-흐름)
3. [파일 구조 맵](#3-파일-구조-맵)
4. [에이전트 프롬프트 튜닝](#4-에이전트-프롬프트-튜닝)
5. [도구(Tool) 수정](#5-도구tool-수정)
6. [에이전트 추가/제거](#6-에이전트-추가제거)
7. [모델 변경](#7-모델-변경)
8. [환경 변수 레퍼런스](#8-환경-변수-레퍼런스)
9. [Claude Code / Codex 사용법](#9-claude-code--codex-사용법)
10. [트러블슈팅](#10-트러블슈팅)

---

## 1. 시스템 아키텍처

### 핵심 개념

Tiny Jarvis는 **에이전트 오케스트레이션 시스템**입니다.
사람이 코드를 작성하는 것이 아니라, AI 에이전트들이 실제 소프트웨어 개발팀처럼 동작합니다.

```
┌──────────────────────────────────────────────────────┐
│                    run.py (오케스트레이터)              │
│                                                      │
│  1. Ollama 상태 확인                                   │
│  2. 제품 저장소 클론                                    │
│  3. GitHub 라벨 생성                                   │
│  4. 부트스트랩 이슈 생성 (최초 1회)                      │
│  5. 사이클 루프 시작:                                   │
│     ┌─────────────────────────────────────────┐       │
│     │  PM 에이전트 실행 (계획)                   │       │
│     │       ↓                                  │       │
│     │  work_plan.json 읽기                     │       │
│     │       ↓                                  │       │
│     │  할당된 에이전트 순차 실행                   │       │
│     │  (Architect → Backend → QA 등)           │       │
│     │       ↓                                  │       │
│     │  각 턴 후 미커밋 변경사항 자동 push          │       │
│     └─────────────────────────────────────────┘       │
│     → 다음 사이클 반복                                  │
└──────────────────────────────────────────────────────┘
```

### 데이터 흐름

```
에이전트 → Google ADK Runner → LiteLLM → Ollama → 로컬 Gemma 모델
  ↕                                                    ↕
도구 호출 (함수)                                    응답 텍스트
  ↕
GitHub (이슈/PR)  ←→  제품 저장소 (파일/커밋)
```

### 주요 컴포넌트

| 컴포넌트 | 파일 | 역할 |
|---------|------|------|
| 오케스트레이터 | `run.py` | 사이클 루프, 에이전트 턴 관리, 안전 종료 |
| 설정 | `config.py` | 모델, 리포, 타임아웃 등 중앙 설정 |
| 에이전트 정의 | `app/agents.py` | 각 에이전트의 모델, 프롬프트, 도구 할당 |
| 프롬프트 | `app/prompts/*.py` | 에이전트별 행동 지침 (시스템 프롬프트) |
| 도구 | `app/tools/*.py` | 에이전트가 호출할 수 있는 함수들 |

---

## 2. 사이클 실행 흐름

### 한 사이클의 상세 흐름

```
사이클 N 시작
│
├─ 1단계: main 브랜치로 체크아웃 + pull
│
├─ 2단계: PM 에이전트 실행
│   ├─ get_project_status() 호출 → 현재 상태 파악
│   ├─ list_open_issues() → 각 역할별 미해결 이슈 확인
│   ├─ 필요시 새 이슈 생성 (create_issue)
│   ├─ work_plan.json 작성 (write_file)
│   ├─ docs/progress.md 업데이트
│   └─ git_commit_and_push
│
├─ 3단계: work_plan.json 파싱
│   └─ 예: [{"role":"backend","turns":3}, {"role":"qa","turns":1}]
│
├─ 4단계: 할당된 에이전트 순차 실행
│   ├─ Backend 턴 1/3:
│   │   ├─ main으로 체크아웃 + pull
│   │   ├─ list_open_issues(label='role:backend') → 작업 찾기
│   │   ├─ 코드 작성, 커밋, PR 생성
│   │   └─ flush_and_push (미커밋 변경사항 자동 push)
│   ├─ Backend 턴 2/3: ...
│   ├─ Backend 턴 3/3: ...
│   └─ QA 턴 1/1:
│       ├─ list_pull_requests → 열린 PR 확인
│       ├─ PR 브랜치로 전환, 코드 리뷰
│       ├─ run_pytest, run_ruff 실행
│       └─ qa:approved 또는 qa:changes-requested 라벨 부여
│
└─ 사이클 N 종료 → 대기 후 사이클 N+1
```

### 안전장치

| 안전장치 | 설명 |
|---------|------|
| 도구 호출 제한 | 에이전트당 최대 30회 도구 호출 |
| 유휴 루프 감지 | 도구 호출 없이 텍스트만 2회 연속 → 턴 종료 |
| 토큰 누출 감지 | `<\|im_start\|>` 등 제어 토큰 → 턴 종료 |
| 타임아웃 | 에이전트당 기본 1800초 (30분) |
| 안전 종료 | Ctrl+C 1회 → 현재 턴 후 종료, 2회 → 강제 종료 |

---

## 3. 파일 구조 맵

```
tiny-jarvis/
│
├── run.py                          ← 수정: 사이클 로직, 부트스트랩 이슈
├── config.py                       ← 수정: 기본값, 역할 목록
├── .env                            ← 수정: 런타임 설정 (모델, 리포)
├── .env.example                    ← 참고: .env 템플릿
├── pyproject.toml                  ← 수정: 의존성 추가/제거
├── CLAUDE.md                       ← 수정: AI 어시스턴트 컨텍스트
│
├── app/
│   ├── agents.py                   ← ★ 핵심: 에이전트 정의 + 도구 매핑
│   │
│   ├── prompts/                    ← ★ 튜닝 포인트: 에이전트 행동 변경
│   │   ├── pm.py                   ← PM 프롬프트 (작업 계획 로직)
│   │   ├── architect.py            ← Architect 프롬프트 (설계/머지 규칙)
│   │   ├── backend.py              ← Backend 프롬프트 (코딩 가이드라인)
│   │   └── qa.py                   ← QA 프롬프트 (리뷰 기준)
│   │
│   └── tools/                      ← 도구 구현 (함수들)
│       ├── files.py                ← 파일 읽기/쓰기/검색
│       ├── git.py                  ← Git 브랜치/커밋/머지/충돌 해결
│       ├── github.py               ← GitHub 이슈/PR (gh CLI 래퍼)
│       ├── project_state.py        ← 프로젝트 상태 종합 스냅샷
│       ├── python_dev.py           ← Python 개발 도구 (uv, pytest, ruff)
│       └── web.py                  ← 웹 검색 (DuckDuckGo) + 내용 추출
│
├── product-repo/                   ← 에이전트가 작업하는 제품 저장소 (자동 클론)
├── docs/                           ← 이 가이드 문서
└── tests/                          ← 에이전트 시스템 자체 테스트
```

### 어떤 파일을 수정해야 하나요?

| 목적 | 수정할 파일 |
|------|-----------|
| 에이전트의 행동 방식 변경 | `app/prompts/*.py` |
| 에이전트에 도구 추가/제거 | `app/agents.py` |
| 새 도구 함수 생성 | `app/tools/새파일.py` + `app/agents.py`에 import |
| 새 에이전트 역할 추가 | `config.py` + `app/prompts/새역할.py` + `app/agents.py` |
| LLM 모델 변경 | `.env`의 `AGENT_MODEL` |
| 타임아웃/사이클 간격 조정 | `.env`의 `AGENT_TIMEOUT`, `CYCLE_INTERVAL` |
| 제품 저장소 변경 | `.env`의 `PRODUCT_REPO`, `PRODUCT_REPO_DIR` |
| 부트스트랩(초기) 이슈 변경 | `run.py`의 `bootstrap_repo()` 함수 |

---

## 4. 에이전트 프롬프트 튜닝

프롬프트는 에이전트의 **두뇌**입니다. 행동, 우선순위, 작업 방식을 결정합니다.

### 파일 위치

```
app/prompts/
├── pm.py           # PM_INSTRUCTION 변수
├── architect.py    # ARCHITECT_INSTRUCTION 변수
├── backend.py      # BACKEND_INSTRUCTION 변수
└── qa.py           # QA_INSTRUCTION 변수
```

### 프롬프트 구조

각 프롬프트는 동일한 패턴을 따릅니다:

```python
# app/prompts/backend.py
BACKEND_INSTRUCTION = """\
You are the Backend Developer of tiny-jarvis — an autonomous AI software engineering team.

IDENTITY:
- Role: Backend Developer
- Tag: [Backend]
...

CYCLE WORKFLOW (follow these steps IN ORDER):
1. CHECK FOR REJECTED PRs ...
2. CHECK YOUR ISSUES ...
3. FOR EACH ISSUE — STANDARD WORKFLOW: ...

CODING STANDARDS:
...

RULES:
...
"""
```

### 프롬프트 수정 예시

**예시 1: Backend 에이전트에 새 코딩 가이드라인 추가**

```python
# app/prompts/backend.py의 CODING STANDARDS 섹션에 추가:

CODING STANDARDS:
- Write REAL working code. No stubs, no "pass", no "TODO".
- Type hints on all function signatures.
+ - Use async/await for all I/O-bound operations.
+ - All database functions must be wrapped in try/except with specific exceptions.
```

**예시 2: PM의 작업 할당 방식 변경**

```python
# app/prompts/pm.py의 TURN ALLOCATION GUIDELINES 수정:

TURN ALLOCATION GUIDELINES:
- Architect designing system / reviewing PRs → 1-2 turns
- Backend implementing Python modules → 3-4 turns
+ - Backend implementing Python modules → 4-5 turns (increase for complex modules)
- QA reviewing PRs and running tests → 1-2 turns
+ - QA reviewing PRs and running tests → 2-3 turns (more thorough reviews)
```

**예시 3: QA의 리뷰 기준 강화**

```python
# app/prompts/qa.py의 REVIEW CRITERIA에 추가:

### Security:
- [ ] SQL uses parameterized queries ONLY
+ - [ ] All user inputs are sanitized before use
+ - [ ] No eval() or exec() calls in the code
```

### 프롬프트 작성 팁

1. **구체적으로 작성**: "좋은 코드를 작성하라" → "모든 함수에 타입 힌트를 추가하라"
2. **순서를 명시**: "다음 단계를 순서대로 따르라" + 번호 매기기
3. **금지 사항을 명확히**: "절대 ... 하지 마라" 형식으로 제약 조건 명시
4. **라벨명은 정확히**: `role:backend` (O) / `backend` (X) / `role: backend` (X)
5. **도구 호출 명시**: "call `함수명`" 형태로 에이전트가 어떤 도구를 써야 하는지 알려주기

---

## 5. 도구(Tool) 수정

### 도구란?

도구는 에이전트가 호출할 수 있는 **Python 함수**입니다.
에이전트가 "파일을 읽고 싶다"고 판단하면 `read_file("main.py")`을 호출합니다.

### 기존 도구 수정

**예시: `run_pytest`에 커버리지 옵션 추가**

```python
# app/tools/python_dev.py

def run_pytest(args: str = "tests/ -v", coverage: bool = False) -> str:
    """Run pytest in the product repository via uv.

    Args:
        args: Arguments to pass to pytest (default: 'tests/ -v').
        coverage: If True, add --cov flag for coverage report.
    """
    cmd = ["uv", "run", "pytest"] + args.split()
    if coverage:
        cmd.extend(["--cov", "--cov-report=term-missing"])
    # ... 나머지 동일
```

### 새 도구 생성

**1단계: 도구 함수 작성**

```python
# app/tools/docker.py (새 파일)
"""Docker 도구 — 컨테이너 빌드/실행"""
from __future__ import annotations

import json
import subprocess

from config import Config

_config = Config.from_env()
_CWD = str(_config.product_repo_dir)


def docker_build(tag: str = "tiny-jarvis:latest") -> str:
    """Build a Docker image for the product.

    Args:
        tag: Docker image tag. Default 'tiny-jarvis:latest'.

    Returns:
        JSON string with build output.
    """
    try:
        result = subprocess.run(
            ["docker", "build", "-t", tag, "."],
            cwd=_CWD, capture_output=True, text=True, timeout=300,
        )
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": result.stdout.strip()[:3000],
            "stderr": result.stderr.strip()[:1000],
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

**2단계: `app/agents.py`에 import 및 할당**

```python
# app/agents.py에 추가:

from app.tools.docker import docker_build  # noqa: E402

# 원하는 에이전트의 tools 리스트에 추가:
backend_agent = Agent(
    name="backend_agent",
    model=_model,
    instruction=BACKEND_INSTRUCTION,
    tools=[
        *_shared_tools,
        # ... 기존 도구들 ...
        docker_build,  # ← 새 도구 추가
    ],
)
```

### 도구 설계 규칙

1. **반환값은 항상 JSON 문자열**: `json.dumps({"success": True/False, ...})`
2. **독스트링 필수**: Google ADK가 독스트링을 LLM에 전달하여 도구 사용법을 알려줌
3. **타입 힌트 필수**: 매개변수 타입을 명시해야 ADK가 올바르게 전달
4. **타임아웃 설정**: 외부 명령 호출 시 반드시 timeout 지정
5. **에러 처리**: 예외 발생 시 `{"success": False, "error": "..."}` 반환

---

## 6. 에이전트 추가/제거

### 새 에이전트 추가 (예: DevOps 에이전트)

**1단계: config.py에 역할 추가**

```python
# config.py
agent_roles: tuple[str, ...] = (
    "pm", "architect", "backend", "qa", "devops",  # ← 추가
)

role_labels: dict[str, str] = field(default_factory=lambda: {
    "pm": "role:pm",
    "architect": "role:architect",
    "backend": "role:backend",
    "qa": "role:qa",
    "devops": "role:devops",  # ← 추가
})
```

**2단계: 프롬프트 파일 생성**

```python
# app/prompts/devops.py
DEVOPS_INSTRUCTION = """\
You are the DevOps Engineer of tiny-jarvis — an autonomous AI software engineering team.

IDENTITY:
- Role: DevOps Engineer
- Tag: [DevOps]
...

CYCLE WORKFLOW:
1. ...
2. ...

RULES:
- ...
"""
```

**3단계: agents.py에 에이전트 등록**

```python
# app/agents.py

from app.prompts.devops import DEVOPS_INSTRUCTION  # noqa: E402

devops_agent = Agent(
    name="devops_agent",
    model=_model,
    instruction=DEVOPS_INSTRUCTION,
    tools=[
        *_shared_tools,
        close_issue,
        write_file,
        git_create_branch, git_switch_branch,
        git_commit_and_push, git_pull,
        create_pull_request,
        run_command,
    ],
)

AGENTS = {
    "pm": pm_agent,
    "architect": architect_agent,
    "backend": backend_agent,
    "qa": qa_agent,
    "devops": devops_agent,  # ← 추가
}
```

**4단계: PM 프롬프트에 새 역할 인식 추가**

```python
# app/prompts/pm.py의 라벨 목록에 추가:
#   Roles: role:pm, role:architect, role:backend, role:qa, role:devops
```

### 에이전트 제거

위 과정의 역순입니다:
1. `AGENTS` 딕셔너리에서 제거
2. `config.py`의 `agent_roles`와 `role_labels`에서 제거
3. 프롬프트 파일 삭제 (선택)

---

## 7. 모델 변경

### Ollama 모델 변경

```bash
# .env 파일 수정
AGENT_MODEL=qwen3:32b    # 또는 다른 Ollama 모델

# 모델 다운로드
ollama pull qwen3:32b
```

### 지원되는 모델 예시

| 모델 | 크기 | 특징 |
|------|------|------|
| `gemma4:31b` | 31B | 기본값, 균형 잡힌 성능 |
| `qwen3:32b` | 32B | 코드 생성 강점 |
| `llama3.3:70b` | 70B | 높은 품질, 느린 속도 |
| `gemma4:12b` | 12B | 빠른 속도, 낮은 품질 |

### 컨텍스트 윈도우 조정

```bash
# .env
NUM_CTX=32768    # 기본값
NUM_CTX=65536    # 더 긴 컨텍스트 (더 많은 VRAM 필요)
NUM_CTX=16384    # 메모리 절약
```

---

## 8. 환경 변수 레퍼런스

| 변수 | 필수 | 기본값 | 설명 |
|------|------|-------|------|
| `PRODUCT_REPO` | O | `user/tiny-jarvis-product` | GitHub 리포지토리 슬러그 |
| `PRODUCT_REPO_DIR` | O | `./product-repo` | 제품 저장소 로컬 경로 |
| `DEFAULT_BRANCH` | - | `main` | 기본 브랜치명 |
| `AGENT_MODEL` | - | `gemma4:31b` | Ollama 모델명 |
| `CYCLE_INTERVAL` | - | `0` | 사이클 간 대기 시간 (초) |
| `AGENT_TIMEOUT` | - | `1800` | 에이전트 턴 타임아웃 (초) |
| `NUM_CTX` | - | `32768` | LLM 컨텍스트 윈도우 크기 |

---

## 9. Claude Code / Codex 사용법

이 프로젝트에는 `CLAUDE.md` 파일이 포함되어 있어
Claude Code나 OpenAI Codex가 프로젝트 구조와 규칙을 즉시 이해합니다.

### Claude Code로 작업하기

```bash
# 프로젝트 디렉토리에서 Claude Code 실행
cd tiny-jarvis
claude
```

#### 유용한 요청 예시

**프롬프트 수정:**
```
"Backend 에이전트의 프롬프트에서 코딩 표준 섹션에
async/await 패턴 가이드라인을 추가해줘"
```

**새 도구 생성:**
```
"에이전트가 SQLite 데이터베이스를 직접 조회할 수 있는
db_query 도구를 app/tools/database.py에 만들어줘"
```

**새 에이전트 추가:**
```
"Frontend 에이전트를 추가하고 싶어. React 컴포넌트를
작성할 수 있도록 config.py, agents.py, prompts/ 모두 설정해줘"
```

**디버깅:**
```
"run.py에서 에이전트 턴이 끝나도 flush_and_push가 작동하지 않는 것 같아.
코드를 확인하고 수정해줘"
```

### Codex로 작업하기

OpenAI Codex (또는 Codex CLI)도 동일한 방식으로 사용 가능합니다.
프로젝트 루트에서 실행하면 `CLAUDE.md`의 컨텍스트를 활용합니다.

```bash
cd tiny-jarvis
codex  # 또는 해당 CLI 명령
```

### CLAUDE.md 커스터마이징

`CLAUDE.md`는 AI 어시스턴트가 프로젝트를 이해하는 데 사용하는 파일입니다.
프로젝트가 변경되면 이 파일도 업데이트하세요:

```markdown
# 추가할 내용 예시:

## 새로 추가된 도구
- `app/tools/database.py` — SQLite 직접 조회 도구

## 변경된 규칙
- Backend 에이전트는 반드시 async/await 패턴을 사용해야 합니다
```

---

## 10. 트러블슈팅

### 자주 발생하는 문제

**문제: "Cannot reach Ollama"**
```
해결: ollama serve가 실행 중인지 확인
      별도 터미널에서: ollama serve
```

**문제: "Failed to clone"**
```
해결: gh auth status로 GitHub 인증 확인
      gh repo view PRODUCT_REPO 로 리포 존재 확인
```

**문제: 에이전트가 이슈를 찾지 못함**
```
해결: GitHub에서 라벨이 정확히 생성되었는지 확인
      role:backend (O) vs role: backend (X) vs backend (X)
      run.py를 재실행하면 라벨이 자동 생성됨
```

**문제: 에이전트가 무한 루프에 빠짐**
```
해결: 30회 도구 호출 제한 + 유휴 루프 감지가 자동으로 턴을 종료합니다.
      그래도 멈추지 않으면 Ctrl+C로 중단하세요.
```

**문제: PermissionError: '/product/...'**
```
해결: .env의 PRODUCT_REPO_DIR을 쓰기 가능한 절대 경로로 변경
      예: /home/사용자/tiny-jarvis/product-repo
```

**문제: 에이전트가 코드를 잘 못 작성함**
```
해결:
1. 더 큰 모델 사용: AGENT_MODEL=qwen3:32b 또는 llama3.3:70b
2. 컨텍스트 윈도우 증가: NUM_CTX=65536
3. 프롬프트에 더 구체적인 코딩 가이드라인 추가
4. Backend 에이전트의 턴 수 증가 (work_plan.json에서 turns 조정)
```

### 로그 읽기

```
16:20:11 [INFO] --- Cycle 1 | PM (planning) ---       ← PM 턴 시작
16:20:15 [INFO] [PM] 🔧 get_project_status()          ← 도구 호출
16:20:16 [INFO] [PM] ← get_project_status: {"open...  ← 도구 응답
16:20:20 [INFO] [PM] 🔧 create_issue({"title":"..."}) ← 이슈 생성
16:21:00 [INFO] [PM] Done in 49.2s                     ← PM 턴 종료
16:21:00 [INFO] Work plan: backendx3, qax1 (4 total)  ← 작업 계획
16:21:01 [INFO] --- Cycle 1 | BACKEND (turn 1/3) ---   ← Backend 시작
```
