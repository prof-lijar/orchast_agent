# Self-Evolving Agent

**Self-Evolving Agent**는 부족한 기능을 스스로 파악하고, 새로운 도구를 설계하며, Python 코드를 생성하고, 샌드박스에서 테스트한 뒤, 도구 레지스트리에 등록하여 이후 요청에 재사용하는 AI 에이전트 시스템입니다.

기존 에이전트 시스템이 사전에 정의된 도구에만 의존하는 것과 달리, 이 에이전트는 **필요에 따라 스스로 도구를 생성**하여 안전하고 검증된 파이프라인을 통해 자신의 기능을 확장합니다.

[Google ADK](https://github.com/google/adk-python) (Agent Development Kit) 기반으로 구축되었습니다.

---

## 연구 배경

이 프로젝트는 [강정훈 교수님](https://github.com/jeonghoonkang)이 제안한 **Self-Evolving Agent** 아키텍처를 구현합니다. 사전에 정의된 도구에 제한되지 않고, 에이전트가 자율적으로 부족한 부분을 파악하고 스스로 확장하는 지속적인 기능 확장을 실증합니다.

아키텍처는 멀티 에이전트 설계를 따릅니다:

- **Root Orchestrator**: 시스템을 조율하고 도구 레지스트리를 관리
- **특화 서브 에이전트**: 도구 명세, 코드 생성, 테스트 생성을 담당
- **안전 우선 파이프라인**: 생성된 모든 코드가 실행 전에 검증됨을 보장

장기적으로는 **반도체 제조** 및 **공정 제어** 환경(BerePi, K-CTDM 아키텍처)을 대상으로 하며, 에이전트가 엄격한 안전 제약 내에서 센서 데이터 처리, 통계 분석, 품질 모니터링을 위한 도구를 동적으로 생성할 수 있습니다.

---

## 작동 방식

사용자가 요청을 보내면, 에이전트는 다음과 같은 결정 루프를 따릅니다:

```
사용자 요청
     ↓
Root Orchestrator Agent
     ↓
┌─── 어떤 동작? ─────────────────────────────────────────┐
│                                                         │
│  사용           생성            수정           삭제      │
│   ↓              ↓              ↓              ↓       │
│  레지스트리    도구 생성      도구 생성      레지스트리  │
│  검색          파이프라인     파이프라인     에서 삭제   │
│   ↓           (명세→코드    (update_mode)   + 파일     │
│  도구          →테스트→등록)      ↓          삭제      │
│  실행              ↓         기존 항목+파일              │
│   ↓          안전성+샌드박스 덮어쓰기                    │
│  결과         검증           (버전 증가)                 │
│  반환              ↓                                    │
│                등록/재시도                                │
└─────────────────────────────────────────────────────────┘
```

### 다이어그램
<img width="1448" height="1086" alt="ChatGPT Image May 12, 2026, 11_25_26 AM" src="https://github.com/user-attachments/assets/2cd106d8-496c-4bb1-b626-91ca2d305fca" />

핵심 포인트: 에이전트는 **단순히 질문에 답하는 것이 아니라**, 세션 간에 지속되는 재사용 가능한 도구를 구축, 수정, 관리합니다. 도구가 한번 생성되고 등록되면, 재생성 없이 이후 모든 요청에서 사용할 수 있습니다.

---

## 아키텍처

### 에이전트

시스템은 Root Orchestrator가 조율하는 **6개의 ADK 에이전트**를 사용합니다:

| 에이전트 | 타입 | 역할 |
|---------|------|------|
| **Root Orchestrator** | `Agent` | 요청 수신, 레지스트리 검색, 기존 도구 사용/생성/수정/삭제 결정 |
| **Tool Spec Agent** | `Agent` | 사용자 요구를 공식적인 JSON 도구 명세(이름, 입력, 출력, 위험 수준, 테스트 케이스)로 변환 |
| **Tool Coder Agent** | `Agent` | 명세로부터 타입 힌트와 독스트링이 포함된 안전한 Python 코드 생성 |
| **Tool Test Agent** | `Agent` | 정상 케이스, 엣지 케이스, 잘못된 입력을 커버하는 pytest 테스트 생성 |
| **Tool Registrar Agent** | `Agent` | 모드에 따라 등록 또는 업데이트를 호출하고 파이프라인 완료를 처리 |
| **Tool Review & Fix Agent** | `Agent` | 실패한 도구 코드나 테스트를 진단하고 수정하여 재시도 |

생성 에이전트는 ADK 세션 상태(`output_key`)를 통해 데이터를 전달하는 **SequentialAgent** 파이프라인으로 구성됩니다:

```
tool_spec_agent (output_key="tool_spec")
       ↓
tool_coder_agent (output_key="tool_code")  ← {tool_spec} 참조
       ↓
tool_test_agent (output_key="tool_tests")  ← {tool_spec}과 {tool_code} 참조
       ↓
tool_registrar_agent  ← 세션 상태에 따라 등록 또는 업데이트 호출
```

### 도구 함수

레지스트리 작업과 도구 실행은 Root Agent의 **결정적(deterministic) 도구 함수**입니다 (LLM 에이전트가 아님):

- `search_registry(query)` — 도구 이름과 설명에서 키워드 검색
- `list_available_tools()` — 등록된 모든 도구 목록 조회
- `execute_registered_tool(tool_name, input_data)` — 등록된 도구를 동적으로 임포트하여 호출
- `register_validated_tool()` — 안전성 검사 → 샌드박스 테스트 → 새 도구 등록
- `update_registered_tool()` — 안전성 검사 → 샌드박스 테스트 → 기존 도구 덮어쓰기 (버전 자동 증가)
- `delete_registered_tool(tool_name)` — 레지스트리에서 도구 제거 및 소스 파일 삭제

### 보조 모듈

| 모듈 | 기능 |
|------|------|
| **Registry Manager** (`app/registry/manager.py`) | JSON 기반 도구 저장소 - 로드, 저장, 검색, 등록, 수정, 삭제, 목록 조회 |
| **Safety Policy** (`app/safety/policy.py`) | AST 기반 임포트 검사, 키워드 스캔, 위험도 분류 |
| **Sandbox Runner** (`app/sandbox/runner.py`) | 서브프로세스 기반 제한된 코드 실행 (타임아웃 및 격리) |

---

## 안전성

생성된 모든 도구는 등록 전에 **3단계 검증 파이프라인**을 통과합니다:

### 1. 정적 안전성 분석 (AST)

안전 정책은 Python의 `ast` 모듈을 사용하여 생성된 코드를 파싱하고, 차단된 모듈을 임포트하거나 위험한 함수를 사용하는 코드를 거부합니다.

**차단된 임포트:**
`os`, `subprocess`, `socket`, `shutil`, `pathlib`, `paramiko`, `ftplib`, `smtplib`, `sys`, `ctypes`

**허용된 네트워크 임포트:** `requests`, `httpx`, `urllib` (웹 데이터 수집 도구용)

**차단된 키워드:**
`eval()`, `exec()`, `open()`, `__import__()`, `system()`, `popen()`, `compile()`, `globals()`, `locals()`

### 2. 샌드박스 테스트 실행

생성된 코드와 테스트는 다음과 같은 **격리된 서브프로세스**에서 실행됩니다:
- 실행 타임아웃 (30초)
- 별도의 작업 디렉토리
- 메인 에이전트와의 프로세스 수준 격리

### 3. 위험도 분류

| 위험 수준 | 정책 | 예시 |
|----------|------|------|
| **Low** | 자동 허용 | 텍스트 변환, 단어 수 세기, JSON 포맷팅, 수학 연산 |
| **Medium** | 승인 필요 (향후) | 파일 읽기, API 요청, 데이터베이스 읽기 |
| **High** | 차단 | 셸 실행, 파일 삭제, 자격 증명 접근 |

v0.1에서는 `low` 위험 도구만 자동 등록이 가능합니다.

**핵심 원칙:** *검증 없이 생성된 코드를 실행하거나 등록하지 않습니다.*

---

## 도구 레지스트리

레지스트리는 검증된 각 도구의 메타데이터를 저장하는 JSON 파일(`app/registry/registry.json`)입니다:

```json
{
  "word_count_tool": {
    "name": "word_count_tool",
    "description": "Counts words in a text string.",
    "module": "app.tools.generated.word_count_tool",
    "function": "word_count_tool",
    "input_schema": { "text": "string" },
    "output_schema": { "word_count": "integer" },
    "risk_level": "low",
    "created_at": "2026-05-10T00:00:00+00:00",
    "version": 1
  }
}
```

도구가 등록되면 Python 소스 파일이 `app/tools/generated/`에 작성되고, 실행 시 `importlib`를 통해 동적으로 로드됩니다.

---

## 도구 생명주기

### 도구 생성

```
1. 사용자 요청: "이 문단의 문장 수를 세어줘."
2. Root Agent가 레지스트리 검색 → 일치하는 도구 없음
3. Root Agent가 tool_creation_pipeline으로 전환
4. Tool Spec Agent가 JSON 명세 생성
5. Tool Coder Agent가 명세로부터 Python 함수 생성
6. Tool Test Agent가 pytest 테스트 생성
7. Tool Registrar Agent가 register_validated_tool 호출:
   a. 안전 정책이 코드 검사 (AST 임포트 스캔 + 키워드 스캔)
   b. 샌드박스에서 격리된 서브프로세스로 테스트 실행
   c. 모두 통과: .py 파일 작성, 레지스트리에 추가
   d. 테스트 실패: Review & Fix Agent가 진단 후 재시도 (최대 3회)
8. Root Agent가 사용자 입력으로 execute_registered_tool 호출
9. 사용자에게 결과 반환 — 도구는 이제 영구적으로 사용 가능
```

### 도구 수정

```
1. 사용자 요청: "web_search_tool이 스니펫도 반환하도록 업데이트해줘."
2. Root Agent가 레지스트리에서 도구 존재 확인
3. Root Agent가 update_mode를 설정하고 tool_creation_pipeline으로 전환
4. 파이프라인이 새로운 명세, 코드, 테스트 생성
5. Tool Registrar Agent가 update_registered_tool 호출:
   a. 생성과 동일한 안전성 + 샌드박스 검증
   b. 기존 .py 파일과 레지스트리 항목 덮어쓰기
   c. 버전 번호 자동 증가
6. 사용자에게 새 버전의 업데이트된 도구 표시
```

### 도구 삭제

```
1. 사용자 요청: "fake_error_generator_tool을 삭제해줘."
2. Root Agent가 도구 존재 확인
3. Root Agent가 delete_registered_tool 호출
4. 도구의 .py 파일 제거 및 레지스트리 항목 삭제
```

---

## 프로젝트 구조

```
self-evolving-agent/
├── app/
│   ├── __init__.py                 # 앱 내보내기
│   ├── agent.py                    # 전체 에이전트, 도구 함수, 지시문
│   ├── fast_api_app.py             # FastAPI 서버 래퍼
│   ├── app_utils/
│   │   ├── typing.py               # Pydantic 모델 (ToolSpec, RegistryEntry, SandboxResult)
│   │   └── telemetry.py            # OpenTelemetry 설정
│   ├── registry/
│   │   ├── manager.py              # 레지스트리 CRUD 작업
│   │   └── registry.json           # 도구 레지스트리 데이터
│   ├── sandbox/
│   │   └── runner.py               # 격리된 코드 실행
│   ├── safety/
│   │   └── policy.py               # 정적 분석 + 위험도 분류
│   └── tools/
│       └── generated/              # 자동 생성된 도구 Python 파일
├── tests/
│   ├── unit/
│   │   ├── test_registry.py        # 레지스트리 CRUD 테스트
│   │   ├── test_safety.py          # 안전 정책 테스트
│   │   ├── test_sandbox.py         # 샌드박스 실행 테스트
│   │   └── test_tools.py           # 도구 실행 + 동적 임포트 테스트
│   ├── integration/
│   └── eval/
├── pyproject.toml
├── CLAUDE.md
└── .gitignore
```

---

## 시작하기

### 사전 요구 사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- Google Cloud 인증 설정 (`gcloud auth application-default login`)

### 설치

```bash
cd self-evolving-agent
uv sync
```

### 테스트 실행

```bash
uv run pytest tests/unit/ -v
```

### 에이전트 실행 (인터랙티브 플레이그라운드)

**Gemini 사용 (기본):**

```bash
agents-cli playground --port 8080
```

브라우저에서 `http://localhost:8080`을 열고 `app` 에이전트를 선택합니다.

**로컬 LLM 사용 (Ollama):**

```bash
AGENT_MODEL=qwen3:32b agents-cli playground --port 8080
```

---

### 로컬 LLM 모델로 실행하기 (Ollama)

이 에이전트는 [Ollama](https://ollama.com/)의 OpenAI 호환 API를 통해 로컬 LLM 모델을 지원합니다. 이를 통해 오프라인 환경이나 자체 GPU 서버에서 전체 시스템을 실행할 수 있습니다.

#### 사전 요구 사항

1. 머신 또는 GPU 서버에 [Ollama](https://ollama.com/download) 설치
2. 모델 다운로드:
   ```bash
   ollama pull qwen3:32b
   ```

#### 작동 방식

에이전트는 ADK의 `LiteLlm` 래퍼를 사용하여 Ollama의 OpenAI 호환 엔드포인트(`/v1/`)를 통해 연결합니다:

```python
LiteLlm(
    model="openai/qwen3:32b",
    api_base="http://localhost:11434/v1",
    api_key="ollama",       # 더미 키 — Ollama는 인증이 필요하지 않음
    num_ctx=8192,            # 대용량 입력이나 파일 처리 시 증가
    repeat_penalty=1.2,
    temperature=0.7,
)
```

`AGENT_MODEL` 환경 변수를 원하는 Ollama 모델명으로 설정하면 에이전트가 나머지를 처리합니다.

#### 테스트된 모델

| 모델 | 도구 호출 | 도구 생성 | 비고 |
|------|:---:|:---:|------|
| **qwen3:32b** | 우수 | 우수 | 로컬 사용 권장 |
| **gemma4:31b** | 작동 | 부분적 | 도구 호출 루프 발생 가능; 안전 콜백으로 처리 |

> 로컬 모델은 함수 호출 안정성이 다양합니다. 에이전트에는 소규모 모델에서 흔한 도구 호출 루프를 감지하고 중단하는 `_limit_tool_loops` 콜백이 포함되어 있습니다.

#### 원격 GPU 서버

Ollama가 원격 서버에서 실행 중인 경우, SSH 포트 포워딩을 사용합니다:

```bash
# 터미널 1: 원격 GPU 서버에서 Ollama 포트 포워딩
ssh -L 11434:localhost:11434 user@gpu-server

# 터미널 2: 에이전트 실행
AGENT_MODEL=qwen3:32b agents-cli playground --port 8080
```

#### 로컬 모델 적응

`AGENT_MODEL`이 설정되면, 에이전트가 자동으로 조정합니다:

- **간소화된 지시문** — 로컬 모델에 최적화된 더 짧고 직접적인 프롬프트
- **프롬프트에 레지스트리 포함** — 모델이 `search_registry`를 호출하지 않아도 모든 도구를 볼 수 있도록 전체 도구 레지스트리가 시스템 지시문에 포함
- **도구 루프 방지** — `_limit_tool_loops` 콜백이 모델이 같은 도구를 반복 호출하는 것을 감지하고 결과와 함께 텍스트 응답을 강제
- **파일 업로드 처리** — 업로드된 파일이 `/tmp/adk_uploads/`에 저장되고, 파일 기반 도구(예: `csv_read_tool`)를 위해 파일 경로가 대화에 주입

---

### 예시 프롬프트

플레이그라운드에서 다음을 시도해 보세요:

```
사용 가능한 모든 도구를 나열해줘.
```

```
다음 문장의 단어 수를 세어줘: The quick brown fox jumps over the lazy dog.
```

```
이 텍스트의 문장 수를 세어줘: Hello world. How are you? I am fine. Thanks for asking.
```

```
word_count_tool이 문자 수도 반환하도록 업데이트해줘.
```

```
fake_error_generator_tool을 삭제해줘.
```

---

## 기술 스택

- **[Google ADK](https://github.com/google/adk-python)** — 에이전트 프레임워크 (Agent, SequentialAgent, App)
- **Gemini / 로컬 LLM** — LLM 백본 (Vertex AI를 통한 Gemini 또는 OpenAI 호환 API를 통한 Ollama 모델)
- **[Ollama](https://ollama.com/)** — 로컬 LLM 추론 서버
- **Python `ast` 모듈** — 생성된 코드의 정적 안전성 분석
- **`subprocess`** — 테스트 실행을 위한 샌드박스 격리
- **Pydantic** — 데이터 모델 및 검증
- **pytest** — 테스트 프레임워크 (프로젝트 테스트 및 생성된 도구 테스트 모두)
