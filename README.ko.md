**[English](README.md)**

# Orchast Agent

목적별 AI 에이전트를 모아둔 모노레포입니다. 각 에이전트는 독립된 디렉토리에서 자체 의존성, 배포, 문서를 관리합니다. 주로 [Google ADK](https://adk.dev/)로 구축하며, Gemini와 로컬 LLM을 활용합니다.

<img width="1254" height="1254" alt="Orchast Agent" src="https://github.com/user-attachments/assets/f7f090c3-6d47-4e09-b1f4-b3afcf57fdc1" />

## 에이전트

| 에이전트 | 설명 | 모델 |
|----------|------|------|
| [self-evolving-agent](./self-evolving-agent/) | 런타임에 도구를 설계, 생성, 테스트, 등록하는 자기 진화 에이전트. 데스크톱 GUI(Zig + Svelte) 포함. | Gemini Flash, Ollama |
| [book-writer](./book-writer/) | 목차를 기반으로 밤새 책을 작성하고, 챕터별로 GitHub에 커밋. | Ollama (로컬) |
| [course-generator](./course-generator/) | 주제 설명으로부터 강의, 과제, 평가를 포함한 다국어 강좌 패키지 생성. | Gemini Flash |
| [caveman-compressor](./caveman-compressor/) | 장황한 텍스트를 간결한 원시인 스타일 요약으로 압축. | Gemini Flash |
| [tutorial-debug-agent](./tutorial-debug-agent/) | 단계별 ADK 튜토리얼 및 터미널 에러 디버깅. | Gemini Flash |

## 빠른 시작

```bash
# 사전 요구 사항: uv, gcloud CLI

# 1. 인증
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 2. 에이전트 선택
cd self-evolving-agent  # 또는 다른 에이전트 디렉토리

# 3. 설치 및 실행
uv sync
agents-cli playground   # localhost:8000에서 브라우저 UI
```

각 에이전트의 README에 상세한 설정 방법과 사용법이 있습니다.

## 저장소 구조

```
orchast_agent/
├── self-evolving-agent/   # 도구 생성 에이전트 + 데스크톱 앱
├── book-writer/           # Ollama 기반 야간 도서 생성
├── course-generator/      # 다중 에이전트 강좌 파이프라인
├── caveman-compressor/    # 텍스트 압축 에이전트
├── tutorial-debug-agent/  # ADK 튜토리얼 & 에러 디버거
└── assets/                # 공유 이미지
```

## 사전 요구 사항

| 도구 | 설치 |
|------|------|
| [uv](https://docs.astral.sh/uv/) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [google-agents-cli](https://pypi.org/project/google-agents-cli/) | `uv tool install google-agents-cli` |
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | 링크 참조 |

## 참고 자료

- [Google ADK](https://adk.dev/)
- [google-agents-cli](https://pypi.org/project/google-agents-cli/)
- [ADK GitHub](https://github.com/google/adk-python)
