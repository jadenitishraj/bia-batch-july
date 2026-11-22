"""Configuration works without reading another project's private files."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from backend import ai


class ConfigurationTests(unittest.TestCase):
    def test_environment_overrides_explicit_gemini_file(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / '.env'
            config.write_text('GEMINI_API_KEY=example-placeholder\nGEMINI_MODEL=example-model\n')
            with patch.object(ai, 'GEMINI_ENV', config), patch.dict(os.environ, {}, clear=True):
                self.assertEqual(ai.configuration(), ('example-placeholder', 'example-model'))
                os.environ['GEMINI_API_KEY'] = 'environment-placeholder'
                os.environ['GEMINI_MODEL'] = 'environment-model'
                self.assertEqual(ai.configuration(), ('environment-placeholder', 'environment-model'))

    def test_missing_key_is_a_clear_chat_setup_message(self):
        import asyncio
        async def answer():
            return [chunk async for chunk in ai.reply('Hello', [])]
        with patch.object(ai, 'configuration', return_value=(None, 'example-model')):
            self.assertIn('Configure a Gemini API key', asyncio.run(answer())[0])
