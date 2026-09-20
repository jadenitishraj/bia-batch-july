"""Check the evaluator's reference data and five-score output without paid calls."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from rag_v2.ragas_evaluation import run_ragas_evaluation


class EvaluationTests(unittest.TestCase):
    def test_expected_answer_is_passed_to_ragas(self):
        scores = {'faithfulness': 1.0, 'answer_relevancy': .8,
                  'llm_context_precision_without_reference': .7,
                  'context_recall': .6, 'factual_correctness(mode=f1)': .5}
        with patch('rag_v2.ragas_evaluation.evaluate', return_value=SimpleNamespace(scores=[scores])) as evaluate, \
             patch('rag_v2.ragas_evaluation.get_langchain_llm'), \
             patch('rag_v2.ragas_evaluation.get_langchain_embeddings'):
            result = run_ragas_evaluation('Who?', 'Maya', ['Maya leads the group.'], 'Maya')
            sample = evaluate.call_args.kwargs['dataset'].samples[0]
            self.assertEqual(sample.reference, 'Maya')
            self.assertEqual(sample.response, 'Maya')
            self.assertEqual(len(evaluate.call_args.kwargs['metrics']), 5)
            self.assertEqual(result['context_recall'], .6)
            self.assertEqual(result['factual_correctness'], .5)

    def test_missing_reference_does_not_call_judge(self):
        with patch('rag_v2.ragas_evaluation.evaluate') as evaluate:
            result = run_ragas_evaluation('Who?', 'Maya', ['Maya'], '')
            self.assertIn('error', result)
            evaluate.assert_not_called()
