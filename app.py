from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from rag_chatbot import ConfigManager, DocumentProcessor, EmbeddingManager, VectorStoreManager, RAGChainManager

app = FastAPI(title="Local RAG Chatbot API")

# CORS 설정 (프론트엔드 호스팅 도메인 또는 로컬 테스트 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시에는 프론트엔드 주소로 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 상태를 유지할 변수들
rag_manager = None
is_initialized = False

class ChatRequest(BaseModel):
    query: str

def initialize_rag():
    global rag_manager, is_initialized
    if is_initialized:
        return

    doc_path = os.getenv("RAG_DOC_PATH", "sample.txt")
    if not os.path.exists(doc_path):
        # 문서가 없으면 임시 문서 생성
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("대한민국의 수도는 서울입니다. 서울은 한강을 끼고 있으며 정치, 경제, 문화의 중심지입니다.")

    print(f"[시스템 초기화 중...] 문서: {doc_path}")
    config = ConfigManager()
    doc_processor = DocumentProcessor(config)
    chunks = doc_processor.load_and_split(doc_path)

    emb_manager = EmbeddingManager(config)
    vs_manager = VectorStoreManager(emb_manager)
    vs_manager.create_vector_store(chunks)

    rag_manager = RAGChainManager(config, vs_manager)
    # 첫 로딩 시간 지연을 막기 위해 미리 체인 설정
    rag_manager.setup_chain()
    is_initialized = True
    print("[시스템 초기화 완료]")

@app.on_event("startup")
async def startup_event():
    # 서버 시작 시 무거운 모델 로딩 등을 미리 수행
    initialize_rag()

@app.get("/")
def read_root():
    return {"message": "Local RAG Chatbot API is running. Check /docs for API documentation."}

@app.post("/chat")
def chat(request: ChatRequest):
    global rag_manager
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG system is not initialized.")

    try:
        answer = rag_manager.ask(request.query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
