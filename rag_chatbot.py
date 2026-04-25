import argparse
import logging
import os
import sys
from typing import List, Optional

# Langchain & AI libraries
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from transformers import pipeline

# -----------------------------------------------------------------------------
# 1. 로깅 및 에러 핸들링 (AWSErrorHandler의 로컬 확장판)
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RAGChatbot")

class ErrorHandler:
    """통합 에러 핸들링 클래스 (AWS 예외 처리도 추후 확장 가능하도록 설계)"""
    @staticmethod
    def handle_error(component: str, error: Exception, critical: bool = True):
        error_msg = f"[{component}] 에러 발생: {str(error)}"
        logger.error(error_msg, exc_info=True)
        if critical:
            print(f"\n[치명적 오류] 시스템을 중단합니다: {error_msg}", file=sys.stderr)
            sys.exit(1)

# -----------------------------------------------------------------------------
# 2. 설정 관리
# -----------------------------------------------------------------------------
class ConfigManager:
    """RAG 시스템의 설정을 관리하는 클래스"""
    def __init__(self):
        # 완전 무료 로컬 모드를 위한 설정
        self.chunk_size = 500
        self.chunk_overlap = 50
        # 임베딩 모델 (가볍고 빠른 한국어 지원 모델을 고려, 기본값으로 다국어 모델 사용)
        self.embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        # LLM 모델 (가장 가벼운 텍스트 생성 모델 중 하나 사용, 로컬 리소스 절약)
        self.llm_model_name = "gpt2"

# -----------------------------------------------------------------------------
# 3. 문서 처리
# -----------------------------------------------------------------------------
class DocumentProcessor:
    """문서를 로드하고 청크로 분할하는 클래스"""
    def __init__(self, config: ConfigManager):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

    def load_and_split(self, file_path: str) -> List:
        try:
            logger.info(f"문서 로드 시도: {file_path}")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            logger.info(f"문서 로드 성공 (총 {len(documents)}개 문서)")

            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"문서 분할 완료: 총 {len(chunks)}개의 청크 생성됨")
            return chunks
        except Exception as e:
            ErrorHandler.handle_error("DocumentProcessor", e)
            return []

# -----------------------------------------------------------------------------
# 4. 임베딩 관리
# -----------------------------------------------------------------------------
class EmbeddingManager:
    """임베딩 모델을 초기화하고 관리하는 클래스"""
    def __init__(self, config: ConfigManager):
        self.config = config
        self.embeddings = None

    def get_embeddings(self) -> HuggingFaceEmbeddings:
        if self.embeddings is None:
            try:
                logger.info(f"임베딩 모델 로드 중: {self.config.embedding_model_name}")
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=self.config.embedding_model_name,
                    model_kwargs={'device': 'cpu'}, # 로컬 구동 보장
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info("임베딩 모델 로드 완료")
            except Exception as e:
                ErrorHandler.handle_error("EmbeddingManager", e)
        return self.embeddings

# -----------------------------------------------------------------------------
# 5. 벡터 저장소 관리
# -----------------------------------------------------------------------------
class VectorStoreManager:
    """FAISS를 이용한 벡터 저장소를 관리하는 클래스"""
    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager
        self.vector_store = None

    def create_vector_store(self, chunks: List):
        try:
            logger.info("벡터 저장소(FAISS) 생성 시작...")
            embeddings = self.embedding_manager.get_embeddings()
            self.vector_store = FAISS.from_documents(chunks, embeddings)
            logger.info("벡터 저장소 생성 완료")
        except Exception as e:
            ErrorHandler.handle_error("VectorStoreManager", e)

    def get_retriever(self, search_kwargs: dict = {"k": 3}):
        if self.vector_store is None:
            ErrorHandler.handle_error("VectorStoreManager", Exception("벡터 저장소가 초기화되지 않았습니다."))
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

# -----------------------------------------------------------------------------
# 6. RAG 체인 관리 (LLM)
# -----------------------------------------------------------------------------
class RAGChainManager:
    """LLM을 초기화하고 RAG 체인을 구성하는 클래스"""
    def __init__(self, config: ConfigManager, vector_store_manager: VectorStoreManager):
        self.config = config
        self.vector_store_manager = vector_store_manager
        self.llm = None
        self.chain = None

    def initialize_llm(self):
        try:
            logger.info(f"LLM 로드 중 (로컬 모드): {self.config.llm_model_name}")
            # 메모리 제약 및 빠른 테스트를 위해 gpt2 등 가벼운 모델을 파이프라인으로 래핑
            hf_pipeline = pipeline(
                "text-generation",
                model=self.config.llm_model_name,
                max_new_tokens=100,
                pad_token_id=50256 # gpt2 eos_token_id
            )
            self.llm = HuggingFacePipeline(pipeline=hf_pipeline)
            logger.info("LLM 로드 완료")
        except Exception as e:
            ErrorHandler.handle_error("RAGChainManager.LLM", e)

    def setup_chain(self):
        try:
            if self.llm is None:
                self.initialize_llm()

            system_prompt = (
                "주어진 컨텍스트(Context)를 바탕으로 사용자의 질문에 한국어로 명확하게 답변하세요. "
                "만약 컨텍스트에 답변할 내용이 없다면 '문서에서 해당 내용을 찾을 수 없습니다.'라고 답변하세요.\n\n"
                "컨텍스트:\n{context}"
            )
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])

            retriever = self.vector_store_manager.get_retriever()
            # question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            # self.chain = create_retrieval_chain(retriever, question_answer_chain)
            from langchain_core.runnables import RunnablePassthrough
            from langchain_core.output_parsers import StrOutputParser
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            self.chain = (
                {"context": retriever | format_docs, "input": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )
            logger.info("RAG 체인 구성 완료")
        except Exception as e:
            ErrorHandler.handle_error("RAGChainManager.Chain", e)

    def ask(self, query: str) -> str:
        try:
            if self.chain is None:
                self.setup_chain()

            logger.info(f"질문 처리 중: '{query}'")
            response = self.chain.invoke(query)

            # 파이프라인 응답 구조에서 텍스트 추출 (모델에 따라 다를 수 있음)
            answer = response
            return answer
        except Exception as e:
            logger.error(f"질문 답변 생성 중 오류 발생: {str(e)}", exc_info=True)
            return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다."

# -----------------------------------------------------------------------------
# 메인 실행부 (CLI)
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="단일 파일 프로덕션급 RAG 챗봇 (로컬 무료 모드)")
    parser.add_argument("--docs", type=str, required=True, help="분석할 텍스트 파일 경로 (예: sample.txt)")
    parser.add_argument("--query", type=str, required=True, help="챗봇에게 물어볼 질문")
    parser.add_argument("--verbose", action="store_true", help="상세 로그 출력")

    args = parser.parse_args()

    if not args.verbose:
        logger.setLevel(logging.WARNING)

    print("\n[시스템 초기화 중...]")
    config = ConfigManager()

    doc_processor = DocumentProcessor(config)
    chunks = doc_processor.load_and_split(args.docs)

    if not chunks:
        print("문서 처리에 실패하여 종료합니다.")
        return

    emb_manager = EmbeddingManager(config)
    vs_manager = VectorStoreManager(emb_manager)
    vs_manager.create_vector_store(chunks)

    rag_manager = RAGChainManager(config, vs_manager)

    print(f"\n[질문]: {args.query}")
    print("[답변 생성 중...]")
    answer = rag_manager.ask(args.query)
    print(f"\n[답변]:\n{answer}\n")

if __name__ == "__main__":
    main()
