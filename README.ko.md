**[English](README.md)**

# Orchast Agent

[Google ADK](https://adk.dev/) (Agent Development Kit)로 구축하고 [Google Agents CLI](https://pypi.org/project/google-agents-cli/)로 스캐폴딩한 AI 에이전트 모음입니다. 이 저장소의 각 에이전트는 텍스트 압축부터 인터랙티브 개발자 도구까지 특정 사용 사례를 보여줍니다.

<img width="1254" height="1254" alt="ChatGPT Image May 9, 2026, 09_32_21 PM" src="https://github.com/user-attachments/assets/f7f090c3-6d47-4e09-b1f4-b3afcf57fdc1" />



## Google ADK란?

[Google ADK](https://adk.dev/)는 Google Cloud에서 Gemini 모델을 활용한 AI 에이전트를 구축, 평가, 배포하기 위한 오픈소스 Python 프레임워크입니다. 주요 기능:

- `Agent` — 지시문과 도구를 통해 동작 정의
- `App` — 루트 에이전트를 래핑하는 배포 가능한 단위
- 내장된 평가, 트레이싱, 클라우드 배포 지원

## Agents CLI란?

[`google-agents-cli`](https://pypi.org/project/google-agents-cli/)는 ADK 프로젝트를 위한 커맨드라인 도구입니다. 전체 생명주기를 관리합니다:

| 명령어 | 용도 |
|---|---|
| `agents-cli scaffold create` | 새로운 ADK 프로젝트 생성 |
| `agents-cli install` | `uv`를 통한 프로젝트 의존성 설치 |
| `agents-cli run "prompt"` | 에이전트에 단일 프롬프트 실행 |
| `agents-cli playground` | `localhost:8000`에서 인터랙티브 브라우저 UI 실행 |
| `agents-cli eval run` | LLM-as-judge 평가 실행 |
| `agents-cli deploy` | Agent Runtime, Cloud Run 또는 GKE에 배포 |
| `agents-cli scaffold enhance` | CI/CD 및 Terraform 인프라 추가 |

---

## 이 저장소의 에이전트

### 1. `caveman-compressor`

> 장황한 텍스트를 기술적 의미를 보존하면서 간결한 원시인 스타일의 요약으로 재작성합니다.

- **모델:** Vertex AI를 통한 `gemini-flash-latest`
- **사용 사례:** 회의록, 명세서, 긴 문서를 간결한 글머리 기호로 압축
- **스택:** Google ADK · Agents CLI · Gemini · Vertex AI

[에이전트 보기 →](./caveman-compressor/)

---

### 2. `tutorial-debug-agent`

> Google ADK, Agents CLI, Codex CLI로 AI 에이전트를 구축하는 개발자를 위한 실습 가이드 및 오류 디버거입니다.

- **모델:** Vertex AI를 통한 `gemini-flash-latest`
- **사용 사례:** 단계별 ADK 튜토리얼 + 에러 붙여넣기 터미널 디버깅
- **도구:** `get_tutorial_step`, `analyze_terminal_error`
- **스택:** Google ADK · Agents CLI · Gemini · Vertex AI

[에이전트 보기 →](./tutorial-debug-agent/)

---

## 사전 요구 사항

| 도구 | 용도 | 설치 |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | Python 패키지 매니저 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [google-agents-cli](https://pypi.org/project/google-agents-cli/) | ADK 프로젝트 CLI | `uv tool install google-agents-cli` |
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | GCP 인증 및 API | 링크 참조 |

## 빠른 시작

### 옵션 A — Agents CLI 사용

```bash
# 1. GCP 인증
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 2. 에이전트를 선택하고 의존성 설치
cd caveman-compressor   # 또는 tutorial-debug-agent
agents-cli install

# 3. 프롬프트 실행
agents-cli run "입력 텍스트"

# 4. 또는 인터랙티브 플레이그라운드 실행
agents-cli playground
```

### 옵션 B — ADK CLI (`adk web`) 사용

[ADK CLI](https://adk.dev/)는 Agents CLI 없이 직접 실행할 수 있는 자체 웹 UI를 제공합니다.

```bash
# 1. ADK 설치
pip install google-adk

# 2. GCP 인증
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 3. 에이전트 폴더 선택
cd caveman-compressor   # 또는 tutorial-debug-agent

# 4. ADK 웹 UI 실행
adk web
# http://localhost:8000 에서 열림
```

`adk web`은 에이전트 응답을 실시간으로 스트리밍하고 브라우저에서 도구 호출 추적을 표시합니다 — 에이전트가 각 단계에서 무엇을 하는지 정확히 확인하는 데 유용합니다.

## 스크린샷

### 터미널 — 에이전트 서버 로그
![agents-cli가 실행되면서 실시간 HTTP 요청 추적을 보여주는 터미널 로그](./assets/terminal-logs.png)

### ADK 웹 UI — 튜토리얼 모드
![ADK 웹 UI가 get_tutorial_step 도구 호출로 Step 1: Install the Tools를 안내하는 화면](./assets/adk-web-tutorial.png)

### ADK 웹 UI — 도구 호출 추적
![ADK 웹 UI가 도구 호출 추적 패널이 열린 상태로 Step 2: Authentication을 보여주는 화면](./assets/adk-web-tool-trace.png)

---

## 참고 자료

- [Google ADK 문서](https://adk.dev/)
- [google-agents-cli (PyPI)](https://pypi.org/project/google-agents-cli/)
- [Google ADK GitHub](https://github.com/google/adk-python)
- [Vertex AI — Gemini 모델](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)
- [Codex CLI (OpenAI)](https://github.com/openai/codex)
