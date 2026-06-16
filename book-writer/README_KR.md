# Book Writer Agent (한국어 버전)

[Ollama](https://ollama.com/)를 통해 로컬에서 실행되는 LLM 모델을 사용하여 밤새 자는 동안 전체 책을 집필하는 인공지능 에이전트 시스템입니다. 이제 한국어를 포함한 다양한 언어를 지원합니다.

## ✨ 주요 기능
- **멀티 에이전트 파이프라인**: Outline(개요) → Writer(집필) → Reviewer(검토) → Finalizer(최종 교정)의 4단계 공정을 통해 고품질의 원고를 생성합니다.
- **자동화 워크플로우**: 표제작(TOC)을 기반으로 각 장(Chapter)을 분석하고, 로컬 환경에서 안정적으로 실행되도록 설계되었습니다.
- **다양한 포맷 지원**: JSON, YAML, Plain Text 형태의 목차를 모두 파싱할 수 있습니다.
- **자동 발행 준비**: 제작된 원고는 자동으로 Git에 커밋/push되며, WeasyPrint를 통해 정교하게 디자인된 PDF로 변환됩니다.

## 🚀 기술 스택
- **Core Engine**: Python 3.12+
- **LLM Framework**: LiteLLM (Ollama 연동)
- **Rendering**: WeasyPrint & Pygments (LaTeX 수식 지원)
- **Agent Orchestration**: Google ADK 기반의 시퀀셜 에이전트 구조

## 🛠 설치 및 실행 방법
1. 리포지토리 클론:
   ```bash
   git clone [레포지토리_URL]
   cd book-writer
   ```
2. 환경 설정:
   ```bash
   uv sync  # 또는 pip install -e .
   ```
3. 실행:
   ```bash
   python run_book.py --toc my-book-toc.json --model gemma4:31b
   ```

## 🔗 관련 링크
- **한글 매뉴얼**: [README.md (English)](README.md) 또는 상단에 연결된 한국어 안내 확인
- **기타 정보**: [여기에 필요한 링크를 추가하세요]
