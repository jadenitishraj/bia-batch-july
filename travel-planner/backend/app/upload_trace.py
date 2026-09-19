"""Observable upload orchestration using unmodified RAG functions."""
import asyncio
import json
from pathlib import Path
from fastapi.responses import StreamingResponse
from .documents import rag_lock, STORAGE

STRATEGIES = {
    'markdown': ('MarkdownNodeParser', 'Splits using Markdown headings and document structure.'),
    'html': ('HTMLNodeParser', 'Splits using HTML structure.'),
    'token': ('TokenTextSplitter', '512-token chunks with 50-token overlap. Selected for sparse punctuation or code-like content.'),
    'semantic': ('SemanticSplitterNodeParser', 'Uses embeddings to find changes in meaning; buffer 1, breakpoint percentile 90.'),
}


def trace_ingestion(path, emit):
    from rag_v2.llm import configure_settings
    from rag_v2.parser import parse_file
    from rag_v2.chunker import chunk_document
    from rag_v2.indexer import index_chunks
    with rag_lock:
        configure_settings()
        emit({'type': 'stage', 'message': 'Reading and classifying the document…'})
        parsed = parse_file(str(path))
        if parsed['text'].startswith('Error parsing PDF:'):
            raise ValueError('PDF extraction failed')
        if not parsed['text'].strip():
            raise ValueError('No readable text in document')
        strategy = parsed['chunk_strategy']
        parser, description = STRATEGIES.get(strategy, ('SentenceSplitter', '768-token chunks with 80-token overlap.'))
        emit({'type': 'parsed', 'strategy': strategy, 'parser': parser, 'description': description,
              'characters': len(parsed['text']), 'filename': path.name})
        emit({'type': 'stage', 'message': 'Creating chunks…'})
        chunks = chunk_document(parsed)
        if not chunks:
            raise ValueError('No chunks created')
        emit({'type': 'chunks', 'chunks': chunks})
        emit({'type': 'stage', 'message': 'Saving embeddings to ChromaDB, extracting graph relationships, and saving the BM25 corpus…'})
        index_chunks(chunks)
        # Verify persisted outputs rather than claiming success from log messages.
        import sqlite3
        ids = {c['id'] for c in chunks}
        with sqlite3.connect(f'file:{STORAGE / "chroma/chroma.sqlite3"}?mode=ro', uri=True) as connection:
            saved_ids = {row[0] for row in connection.execute('SELECT embedding_id FROM embeddings')}
        bm25 = json.loads((STORAGE / 'bm25_index.json').read_text())
        bm25_ids = {c['id'] for c in bm25}
        graph_path = STORAGE / 'graph_store.json'
        graph = json.loads(graph_path.read_text()).get('graph_dict', {}) if graph_path.exists() else {}
        emit({'type': 'storage', 'vector_saved': len(ids & saved_ids), 'bm25_saved': len(ids & bm25_ids),
              'expected': len(ids), 'graph_file': graph_path.exists(),
              'graph_relationships': sum(len(edges) for edges in graph.values())})
        if not ids <= saved_ids or not ids <= bm25_ids:
            raise ValueError('Persisted chunk verification failed')
        emit({'type': 'done', 'filename': path.name, 'chunks': len(chunks)})


def upload_stream(path):
    async def events():
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()
        def emit(event):
            loop.call_soon_threadsafe(queue.put_nowait, event)
        def worker():
            try:
                trace_ingestion(path, emit)
            except Exception:
                emit({'type': 'error', 'message': 'Upload could not finish. The stages above show where it stopped. Some data may have been saved; the original RAG code has not been changed.'})
            finally:
                emit(None)
        task = asyncio.create_task(asyncio.to_thread(worker))
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield json.dumps(event) + '\n'
            await task
        finally:
            # Worker finishes persistence even if the browser disconnects.
            if not task.done():
                await asyncio.shield(task)
    return StreamingResponse(events(), media_type='application/x-ndjson', headers={'Cache-Control': 'no-cache'})
