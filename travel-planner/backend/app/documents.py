"""Integration around the untouched rag_v2 package."""
import json
import logging
import threading
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix='/api/documents')
STORAGE = Path(__file__).resolve().parents[1] / 'rag_v2' / '.global_storage'
UPLOADS = Path(__file__).resolve().parents[1] / 'uploads'
rag_lock = threading.Lock()
logger = logging.getLogger(__name__)


def corpus_status():
    path = STORAGE / 'bm25_index.json'
    chunks = json.loads(path.read_text()) if path.exists() else []
    sources = sorted({c.get('metadata', {}).get('source_file', 'Unknown') for c in chunks})
    return {'chunks': len(chunks), 'sources': sources}


@router.get('')
def status():
    with rag_lock:
        return corpus_status()


def ingest(path):
    from rag_v2.pipeline import ingest_file
    with rag_lock:
        result = ingest_file(str(path))
    return result


def retrieve(question):
    from rag_v2.pipeline import search_rag
    with rag_lock:
        if not corpus_status()['chunks']:
            return 'No documents have been indexed. Ask the user to upload a document first.'
        # The original pipeline returns a string. Consume it directly.
        return search_rag(question, top_k=5)


@router.post('/upload')
async def upload(file: UploadFile = File(...), trace: bool = False):
    name = Path((file.filename or '').replace('\\', '/')).name
    if Path(name).suffix.lower() not in {'.pdf', '.txt', '.md'}:
        raise HTTPException(400, 'Choose a PDF, TXT or Markdown file.')
    content = await file.read(20 * 1024 * 1024 + 1)
    await file.close()
    if not content or len(content) > 20 * 1024 * 1024:
        raise HTTPException(400, 'Choose a non-empty file smaller than 20 MB.')
    destination = UPLOADS / uuid4().hex / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    if trace:
        from .upload_trace import upload_stream
        return upload_stream(destination)
    try:
        result = await run_in_threadpool(ingest, destination)
    except Exception as error:
        logger.error('Unmodified RAG upload failed: %s', type(error).__name__)
        raise HTTPException(502, 'The original RAG pipeline could not finish indexing. Some stores may have been updated. The RAG code has not been changed; check the backend output before retrying.') from None
    return {'filename': name, 'chunks': result.get('chunks_created', 0),
            'message': 'Indexing completed.'}
