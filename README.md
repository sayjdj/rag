# RAG Chatbot (단일 파일 프로덕션급 구현)

본 프로젝트는 단일 파일(`rag_chatbot.py`)에 RAG(Retrieval-Augmented Generation) 시스템의 모든 핵심 컴포넌트를 모듈화하여 구현한 완성도 높은 챗봇입니다.

## 주요 특징
- **모듈화된 설계**: 문서 처리, 임베딩, 벡터 저장, LLM 체인을 독립적인 클래스로 분리.
- **비용 완전 무료 (로컬 모드)**: AWS 종속성 없이 로컬 환경에서 HuggingFace 모델과 FAISS를 사용하여 구동 가능.
- **견고한 오류 처리 및 로깅**: 각 단계별 발생 가능한 예외 상황을 안전하게 처리하고 상세한 로그를 남김.

## 요구 사항
* Python 3.9 이상

## 설치 가이드
패키지 설치
```bash
pip install -e .
```
*테스트용 패키지 포함 설치:*
```bash
pip install -e ".[dev]"
```

## 실행 방법 (무료 로컬 모드)
`rag_chatbot.py`는 CLI 인터페이스를 제공하여 쉽게 테스트할 수 있습니다.

### 1. 샘플 문서 생성
RAG 시스템이 참고할 텍스트 파일(예: `sample.txt`)을 생성합니다.

### 2. 단일 질문 실행
```bash
python rag_chatbot.py --docs sample.txt --query "이 문서의 핵심 내용은 무엇인가요?"
```

## 시스템 구조 및 설계
시스템 설계에 대한 자세한 내용은 [RAG_CHATBOT_SPECIFICATION.md](RAG_CHATBOT_SPECIFICATION.md)를 참고하세요.
