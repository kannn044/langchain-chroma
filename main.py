import os
import uuid
import shutil
from typing import Dict, List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from CustomBGEM3FlagModel import CustomBGEM3FlagModel
from FlagEmbedding import FlagReranker

app = FastAPI()
reranker = FlagReranker("BAAI/bge-reranker-large", use_fp16=True)

chunk_size=1024
chunk_overlap=384

embedding_function = CustomBGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
vectorstore_L = Chroma(persist_directory="./vectorstore_L", embedding_function=embedding_function)
vectorstore_M = Chroma(persist_directory="./vectorstore_M", embedding_function=embedding_function)
vectorstore_S = Chroma(persist_directory="./vectorstore_S", embedding_function=embedding_function)

text_splitter_L = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
text_splitter_M = RecursiveCharacterTextSplitter(chunk_size=chunk_size/2, chunk_overlap=chunk_overlap/2)
text_splitter_S = RecursiveCharacterTextSplitter(chunk_size=chunk_size/4, chunk_overlap=chunk_overlap/4)

loader = DirectoryLoader('knowledge_cleaned', loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
docs = sorted(loader.load(), key=lambda x: x.metadata["source"].split("/")[-1])
for i, doc in enumerate(docs):
    text = doc.page_content
    title = f"article{str(i).zfill(3)}"
    doc.metadata["title"] = title
    doc.metadata["filename"] = doc.metadata["source"].split("/")[-1]
    
splits_L = text_splitter_L.split_documents(docs)
splits_M = text_splitter_M.split_documents(docs)
splits_S = text_splitter_S.split_documents(docs)

embedding_function = CustomBGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
storedb = "./vectorstore_L"
if os.path.exists(storedb):
    vectorstore_L: Chroma = Chroma(
        embedding_function=embedding_function, persist_directory=storedb,
        collection_metadata={"hnsw:space": "cosine"},
    )
else:
    vectorstore_L = Chroma.from_documents(
        documents=splits_L,
        persist_directory=storedb,
        embedding=embedding_function,
        collection_metadata={"hnsw:space": "cosine"},
    )

storedb = "./vectorstore_M"
if os.path.exists(storedb):
    vectorstore_M: Chroma = Chroma(
        embedding_function=embedding_function, persist_directory=storedb,
        collection_metadata={"hnsw:space": "cosine"},
    )
else:
    vectorstore_M = Chroma.from_documents(
        documents=splits_M,
        persist_directory=storedb,
        embedding=embedding_function,
        collection_metadata={"hnsw:space": "cosine"},
    )
storedb = "./vectorstore_S"
if os.path.exists(storedb):
    vectorstore_S: Chroma = Chroma(
        embedding_function=embedding_function, persist_directory=storedb,
        collection_metadata={"hnsw:space": "cosine"},
    )
else:
    vectorstore_S = Chroma.from_documents(
        documents=splits_S,
        persist_directory=storedb,
        embedding=embedding_function,
        collection_metadata={"hnsw:space": "cosine"},
    )
    
vectorstore_L.add_documents(splits_L)
vectorstore_M.add_documents(splits_M)
vectorstore_S.add_documents(splits_S)
    
def load_documents(dir_name: str,filename :str):
    loader = DirectoryLoader(dir_name, loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    docs = sorted(loader.load(), key=lambda x: x.metadata["source"].split("/")[-1])
    for i, doc in enumerate(docs):
        doc.metadata["title"] = f"knowledge{str(i).zfill(3)}"
        doc.metadata["filename"] = filename

    splits_L = text_splitter_L.split_documents(docs)
    splits_M = text_splitter_M.split_documents(docs)
    splits_S = text_splitter_S.split_documents(docs)
    return splits_L, splits_M, splits_S

def search_langchain(query: str, top_k: int = 5) -> List[Dict]:
    vectorstores = [vectorstore_L, vectorstore_M, vectorstore_S]
    results = []

    for store in vectorstores:
        matches = store.similarity_search_with_score(query, k=top_k)
        for match in matches:
            print(match[0])
            obj = {
                "title": match[0].metadata["title"],
                "chunk": match[0].page_content,
                "filename": match[0].metadata["filename"],
                "score": reranker.compute_score([query, match[0].page_content]),
                "content": open(f'knowledge_cleaned/{match[0].metadata["filename"]}', 'r', encoding='utf-8').read()
            }
            results.append(obj)   

    best_results = {}
    for result in results:
        filename = result["filename"]
        if filename not in best_results or result["score"] > best_results[filename]["score"]:
            best_results[filename] = result

    return list(best_results.values())

@app.get("/similarity_search")
def similarity_search(query: str, top_k: int = 5) -> Dict:
    results = search_langchain(query, top_k)
    if not results:
        return {"message": "No results found"}
    return {"results": results}

@app.post("/add-documents")
async def create_item(request: Request):
    form_data = await request.form()
    title = form_data.get('title')
    description = form_data.get('description')

    filename = f"knowledge_{uuid.uuid4()}.txt"
    with open(f'document/{filename}', 'w', encoding='utf-8') as f:
        f.write(f"{title}\n\n{description}")

    (L, M, S) = load_documents("document", filename)
    vectorstore_L.add_documents(L)
    vectorstore_M.add_documents(M)
    vectorstore_S.add_documents(S)

    shutil.copy(f'document/{filename}', f'knowledge_cleaned/{filename}')
    # os.renames(f'document/{filename}', f'knowledge_cleaned/{filename}')
    return {"message": "Document added successfully"}

# Start the FastAPI server with:
# uvicorn main:app --host 0.0.0.0 --port 8880