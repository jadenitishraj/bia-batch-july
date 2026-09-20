"""Check graph evidence and its connection to hybrid search without API calls."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from llama_index.core import StorageContext
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.llms import MockLLM
from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from rag_v2.retriever import search_global_db


class GraphRetrievalTests(unittest.TestCase):
    def test_graph_relationship_reaches_search_output(self):
        graph = SimpleGraphStore()
        graph.upsert_triplet('Maya', 'coordinates', 'Walking group')
        storage = StorageContext.from_defaults(graph_store=graph)
        retriever = KnowledgeGraphRAGRetriever(
            storage_context=storage, llm=MockLLM(),
            entity_extract_fn=lambda query: ['Maya'],
            synonym_expand_fn=lambda entity: [],
        )
        evidence = retriever.retrieve('Who does Maya coordinate?')
        self.assertTrue(evidence)
        self.assertIn('Walking group', evidence[0].node.text)

        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'bm25_index.json').write_text(json.dumps([
                {'id': 'test', 'text': 'Maya coordinates the walking group.', 'metadata': {}}
            ]))
            with patch('rag_v2.retriever.GLOBAL_STORAGE_DIR', Path(directory)), \
                 patch('rag_v2.retriever.get_global_storage', return_value=storage), \
                 patch('rag_v2.retriever.get_llama_llm', return_value=MockLLM()), \
                 patch('rag_v2.retriever.get_llama_embed_model'), \
                 patch('rag_v2.retriever.VectorStoreIndex'), \
                 patch('rag_v2.retriever.BM25Retriever'), \
                 patch('rag_v2.retriever.HyDEQueryTransform'), \
                 patch('rag_v2.retriever.QueryFusionRetriever') as fusion, \
                 patch('rag_v2.retriever.LLMRerank') as rerank:
                fusion.return_value.retrieve.return_value = evidence + evidence
                rerank.return_value.postprocess_nodes.return_value = evidence
                result = search_global_db.invoke({'query': 'Who does Maya coordinate?'})
                self.assertEqual(len(fusion.call_args.kwargs['retrievers']), 3)
                self.assertIsInstance(fusion.call_args.kwargs['retrievers'][2], KnowledgeGraphRAGRetriever)
                self.assertEqual(len(rerank.return_value.postprocess_nodes.call_args.args[0]), 1)
                self.assertIn('Walking group', result)
                self.assertIn('Knowledge graph', result)

    def test_empty_graph_returns_no_evidence(self):
        retriever = KnowledgeGraphRAGRetriever(
            storage_context=StorageContext.from_defaults(graph_store=SimpleGraphStore()),
            llm=MockLLM(), entity_extract_fn=lambda query: ['Maya'],
            synonym_expand_fn=lambda entity: [],
        )
        self.assertEqual(retriever.retrieve('Maya'), [])
