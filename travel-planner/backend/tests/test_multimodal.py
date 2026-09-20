import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rag_v2.parser import parse_file, determine_strategy
from rag_v2.chunker import chunk_document

class MultimodalTests(unittest.TestCase):
    def test_json_reader_formats(self):
        records = [{'text': 'A diagram explains retrieval.', 'start': 5, 'duration': 8},
                   {'text': 'The index stores evidence.', 'start': 13, 'duration': 5}]
        for data in [records, {'segments': records}, {'transcript': records}, {'name': 'ordinary JSON'}]:
            with tempfile.TemporaryDirectory() as directory:
                p = Path(directory) / 'captions.json'
                p.write_text(json.dumps(data))
                parsed = parse_file(str(p))
                chunks = chunk_document(parsed)
                self.assertEqual(parsed['chunk_strategy'], 'token')
                self.assertTrue(chunks)
                expected = 'ordinary JSON' if 'name' in data else 'index stores evidence'
                self.assertIn(expected, ' '.join(c['text'] for c in chunks))
                self.assertEqual(chunks[0]['metadata']['source_file'], 'captions.json')

    def test_long_transcript_splits(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'long.srt'
            p.write_text('1\n00:00:10,000 --> 00:01:40,000\n' + 'Retrieval finds relevant evidence. ' * 400)
            chunks = chunk_document(parse_file(str(p)))
            self.assertGreater(len(chunks), 1)
            self.assertTrue(all(c['text'].strip() for c in chunks))

    def test_srt_vtt(self):
        for extension, prefix in [('srt', '1\n'), ('vtt', 'WEBVTT\n\n')]:
            with tempfile.TemporaryDirectory() as directory:
                p = Path(directory) / ('captions.' + extension)
                p.write_text(prefix + '00:00:05.000 --> 00:00:09.000\nHello students.\n')
                parsed = parse_file(str(p))
                chunks = chunk_document(parsed)
                self.assertEqual(chunks[0]['text'], 'Hello students.')
                self.assertEqual(parsed['chunk_strategy'], 'transcript')

    def test_png_meaning_becomes_chunks(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'chart.png'; p.write_bytes(b'test')
            with patch('rag_v2.image_parser.extract_image', return_value='# Chart\nRevenue rises from 10 to 20.'):
                parsed = parse_file(str(p)); chunks = chunk_document(parsed)
            self.assertEqual(parsed['chunk_strategy'], 'image_markdown')
            self.assertTrue(any('Revenue' in c['text'] for c in chunks))

    def test_llamaindex_vision_response(self):
        from PIL import Image
        from llama_index.core.llms import ChatMessage, ChatResponse, ImageBlock
        from rag_v2.image_parser import extract_image
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'chart.png'
            Image.new('RGB', (10, 10), 'white').save(p)
            with patch('rag_v2.image_parser.OpenAI') as model:
                model.return_value.chat.return_value = ChatResponse(
                    message=ChatMessage(role='assistant', content='# Chart\nRevenue rises.'))
                self.assertIn('Revenue rises', extract_image(p))
                messages = model.return_value.chat.call_args.args[0]
                self.assertIsInstance(messages[1].blocks[1], ImageBlock)
                model.return_value.chat.return_value = ChatResponse(
                    message=ChatMessage(role='assistant', content='NO_CONTENT'))
                with self.assertRaisesRegex(ValueError, 'No meaningful'):
                    extract_image(p)

    def test_invalid_png_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'bad.png';p.write_bytes(b'not an image')
            with self.assertRaisesRegex(ValueError, 'readable PNG'):
                parse_file(str(p))

    def test_no_meaning_not_indexed(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'blank.png';p.write_bytes(b'test')
            with patch('rag_v2.image_parser.extract_image', side_effect=ValueError('No meaningful readable content')):
                with self.assertRaises(ValueError): parse_file(str(p))

    def test_existing_strategies(self):
        self.assertEqual(determine_strategy('hello','.md'),'markdown')
        self.assertEqual(determine_strategy('hello','.json'),'token')
        self.assertEqual(determine_strategy('hello','.html'),'html')
