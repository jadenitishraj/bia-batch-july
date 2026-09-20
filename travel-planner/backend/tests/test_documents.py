"""Integration tests around, never edits to, the copied RAG package."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.document_answers import RequestIntent


class DocumentTests(unittest.TestCase):
    def test_rag_source_matches_original_copy(self):
        backend = Path(__file__).resolve().parents[1]
        manifest = json.loads((backend / 'rag_v2-copy-manifest.json').read_text())
        for relative, expected in manifest.items():
            if relative.endswith('.py') and relative not in {'parser.py', 'chunker.py', 'ragas_evaluation.py', 'retriever.py'}:
                actual = hashlib.sha256((backend / 'rag_v2' / relative).read_bytes()).hexdigest()
                self.assertEqual(actual, expected, relative)

    def test_document_only_does_not_run_trip_graph(self):
        with patch('app.main.classify_request', return_value=RequestIntent(travel=False, documents=True)), patch('app.main.answer_documents', return_value={'answer': 'Meet at 9:15. Source: guide.md', 'context': 'Source: guide.md\nMeet at 9:15.'}), patch('app.graph.travel_planner') as graph:
            response = TestClient(app).post('/api/plan', json={'request': 'What time does my document say?'})
        graph.astream.assert_not_called()
        events = [json.loads(line) for line in response.text.splitlines()]
        answer = next(e['answer'] for e in events if e['type'] == 'result')
        self.assertIn('Meet at 9:15', answer)
        self.assertNotIn('CHOSEN FLIGHT', answer)

    def test_mixed_request_appends_document_answer(self):
        class FakeGraph:
            async def astream(self, *args, **kwargs):
                yield {'revision': {'final_plan': 'Original trip answer'}}
        with patch('app.main.classify_request', return_value=RequestIntent(travel=True, documents=True)), patch('app.main.answer_documents', return_value={'answer': 'Document fact', 'context': 'Evidence'}), patch('app.graph.travel_planner', FakeGraph()):
            response = TestClient(app).post('/api/plan', json={'request': 'Plan a trip and use my document'})
        results = [json.loads(line)['answer'] for line in response.text.splitlines() if json.loads(line)['type'] == 'result']
        self.assertEqual(results[-1], 'Original trip answer\n\n---\n\n## From your documents\n\nDocument fact')

    def test_upload_keeps_filename_and_calls_ingestion(self):
        with tempfile.TemporaryDirectory() as directory, patch('app.documents.UPLOADS', Path(directory)), patch('app.documents.ingest', return_value={'chunks_created': 3}) as ingest:
            response = TestClient(app).post('/api/documents/upload', files={'file': ('../guide.md', b'# Guide\nSome text', 'text/markdown')})
            self.assertEqual(response.status_code, 200)
            saved = ingest.call_args.args[0]
            self.assertTrue(saved.is_relative_to(Path(directory)))
            self.assertEqual(saved.name, 'guide.md')
            self.assertEqual(saved.read_bytes(), b'# Guide\nSome text')

    def test_upload_rejects_unsupported_file(self):
        response = TestClient(app).post('/api/documents/upload', files={'file': ('file.exe', b'content')})
        self.assertEqual(response.status_code, 400)

    def test_retrieval_error_preserves_trip_answer(self):
        class FakeGraph:
            async def astream(self, *args, **kwargs):
                yield {'revision': {'final_plan': 'Original trip answer'}}
        with patch('app.main.classify_request', return_value=RequestIntent(travel=True, documents=True)), patch('app.main.answer_documents', side_effect=RuntimeError('private payload')), patch('app.graph.travel_planner', FakeGraph()):
            response = TestClient(app).post('/api/plan', json={'request': 'Plan a trip with documents'})
        self.assertIn('Original trip answer', response.text)
        self.assertIn('Document retrieval failed', response.text)
        self.assertNotIn('private payload', response.text)
