from pathlib import Path

def determine_strategy(text: str, ext: str) -> str:
    """Decide the chunking strategy based on file extension and content heuristics."""
    if ext == ".md":
        return "markdown"
    if ext in (".html", ".htm"):
        return "html"
    if ext in (".log", ".trace", ".json", ".py"):
        return "token"
        
    # Table heavy heuristic
    if text.count("|") > 20 and text.count("\n") > 5:
        return "markdown"
        
    # YouTube script / No grammar heuristic
    # (Lots of text but very few periods or commas)
    word_count = len(text.split())
    punctuation_count = text.count(".") + text.count(",") + text.count("!") + text.count("?")
    if word_count > 50 and punctuation_count < (word_count * 0.05):
        return "token"
        
    return "semantic"

def parse_file(file_path: str) -> dict:
    """Read a file and classify its content type for chunking. Returns a simple dict."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} not found.")
    
    print(f"  → Parsing file: {path.name}...")
    ext = path.suffix.lower()
    
    source_type = 'document'
    if ext == '.png':
        from .image_parser import extract_image
        text = extract_image(path)
        source_type = 'image'
    elif ext == '.pdf':
        from pypdf import PdfReader
        text = '\n\n'.join(page.extract_text() or '' for page in PdfReader(str(path)).pages)
    elif ext == '.json':
        from llama_index.readers.json import JSONReader
        documents = JSONReader().load_data(input_file=str(path))
        text = '\n'.join(document.text for document in documents)
    elif ext in {'.srt', '.vtt'}:
        import pysubs2
        captions = pysubs2.load(str(path), encoding='utf-8-sig')
        text = '\n'.join(caption.plaintext for caption in captions)
        source_type = 'video_transcript'
    else:
        text = path.read_text(encoding='utf-8-sig', errors='replace')
    if not text.strip():
        raise ValueError('No readable content found. Nothing was indexed.')

    # Determine classification using heuristic function
    strategy = 'transcript' if ext in {'.srt', '.vtt'} else ('image_markdown' if ext == '.png' else determine_strategy(text, ext))
        
    print(f"  → Classified as: {strategy} strategy")
    
    return {
        "title": path.name,
        "text": text,
        "chunk_strategy": strategy,
        "metadata": {
            "source_file": path.name,
            "source_type": source_type,
            "extension": ext
        }
    }
