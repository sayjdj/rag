import pytest
import os
from rag_chatbot import (
    ConfigManager,
    DocumentProcessor,
    EmbeddingManager,
    VectorStoreManager,
    RAGChainManager
)

# 테스트용 더미 파일 경로
TEST_FILE_PATH = "test_sample.txt"
TEST_CONTENT = "대한민국의 수도는 서울입니다. 서울은 한강을 끼고 있으며 정치, 경제, 문화의 중심지입니다."

@pytest.fixture(scope="module")
def setup_test_file():
    # 테스트 파일 생성
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)
    yield TEST_FILE_PATH
    # 테스트 종료 후 파일 삭제
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)

@pytest.fixture(scope="module")
def config():
    return ConfigManager()

def test_document_processor(setup_test_file, config):
    doc_processor = DocumentProcessor(config)
    chunks = doc_processor.load_and_split(setup_test_file)

    assert len(chunks) > 0, "문서 청크가 생성되어야 합니다."
    assert "서울" in chunks[0].page_content, "문서 내용이 올바르게 로드되어야 합니다."

def test_embedding_and_vector_store(setup_test_file, config):
    # 문서 로드
    doc_processor = DocumentProcessor(config)
    chunks = doc_processor.load_and_split(setup_test_file)

    # 임베딩 매니저 초기화
    emb_manager = EmbeddingManager(config)
    assert emb_manager.get_embeddings() is not None, "임베딩 모델이 초기화되어야 합니다."

    # 벡터 저장소 생성
    vs_manager = VectorStoreManager(emb_manager)
    vs_manager.create_vector_store(chunks)

    # 검색기(Retriever) 확인
    retriever = vs_manager.get_retriever(search_kwargs={"k": 1})
    results = retriever.invoke("수도는 어디인가요?")

    assert len(results) > 0, "검색 결과가 존재해야 합니다."
    assert "서울" in results[0].page_content, "검색된 문서에 정답 키워드가 포함되어야 합니다."

# LLM 체인 테스트는 모델 다운로드 및 실행 시간이 오래 걸릴 수 있으므로
# 시스템이 끝까지 돌아가는지(파이프라인 구축) 여부만 가볍게 검증합니다.
def test_rag_chain_initialization(setup_test_file, config):
    doc_processor = DocumentProcessor(config)
    chunks = doc_processor.load_and_split(setup_test_file)

    emb_manager = EmbeddingManager(config)
    vs_manager = VectorStoreManager(emb_manager)
    vs_manager.create_vector_store(chunks)

    rag_manager = RAGChainManager(config, vs_manager)
    rag_manager.setup_chain()

    assert rag_manager.chain is not None, "RAG 체인이 성공적으로 구성되어야 합니다."
