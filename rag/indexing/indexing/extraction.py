"""
Document extraction — converts files of all supported formats to (markdown_content, docling_document).

Supports:
- PDF, DOCX, PPTX, XLSX, HTML via Docling (primary)
- PDF fallback via PyMuPDF + RapidOCR (scanned pages)
- Audio (MP3, WAV, M4A, FLAC) via Whisper ASR through Docling
- Plain text / Markdown read directly
- Stub record as last resort
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Handles document format conversion. Singleton-initialised per pipeline run."""

    def __init__(self, cache_dir: str = "indexing_cache", skip_cache: bool = False):
        self._docling_converter = None
        self._rapidocr_reader = None
        self.cache_dir = Path(cache_dir)
        self.skip_cache = skip_cache
        self.cache_dir.mkdir(exist_ok=True)

    def _cache_path(self, file_path: str) -> Path:
        """Return the cache file path for a given document."""
        safe = str(file_path).replace("/", "__").replace("\\", "__").replace(" ", "_")
        return self.cache_dir / f"{safe}.json"

    def _load_cache(self, file_path: str) -> Optional[tuple[str, Any]]:
        """Load cached Docling parse if file_mtime matches. Returns (markdown, docling_doc) or None."""
        if self.skip_cache:
            return None
        cache_path = self._cache_path(file_path)
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            current_mtime = str(os.path.getmtime(file_path))
            if data.get("file_mtime") != current_mtime:
                return None
            from docling_core.types.doc import DoclingDocument
            docling_doc = DoclingDocument.model_validate(data["document"])
            return (data["markdown"], docling_doc)
        except Exception as e:
            logger.warning(f"Cache load failed for {os.path.basename(file_path)}: {e}")
            return None

    def _save_cache(self, file_path: str, markdown: str, docling_doc: Any) -> None:
        """Save Docling parse result to disk cache."""
        try:
            cache_path = self._cache_path(file_path)
            data = {
                "file_mtime": str(os.path.getmtime(file_path)),
                "markdown": markdown,
                "document": docling_doc.model_dump(),
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            logger.info(f"Saved extraction cache: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Cache save failed for {os.path.basename(file_path)}: {e}")

    def get_converter(self):
        """Return a shared DocumentConverter, initialising it once and reusing across all files."""
        if self._docling_converter is None:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
            logger.info("Initialising Docling DocumentConverter (one-time, shared for all files)...")
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.do_table_structure = True
            pipeline_options.ocr_options = RapidOcrOptions()
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import PdfFormatOption
            self._docling_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            logger.info("Docling DocumentConverter ready (RapidOCR, smart page detection)")
        return self._docling_converter

    def read_document(self, file_path: str) -> tuple[str, Optional[Any]]:
        """
        Read document content from file — supports multiple formats via Docling.

        Returns:
            Tuple of (markdown_content, docling_document).
            docling_document is None for text files and audio files.
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        # Audio formats — transcribe with Whisper ASR
        audio_formats = ['.mp3', '.wav', '.m4a', '.flac']
        if file_ext in audio_formats:
            content = self.transcribe_audio(file_path)
            return (content, None)

        # Docling-supported formats (convert to markdown)
        docling_formats = ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.html', '.htm']

        if file_ext in docling_formats:
            # --- Cache check ---
            cached = self._load_cache(file_path)
            if cached:
                logger.info(f"Cache hit (skipping Docling): {os.path.basename(file_path)}")
                return cached

            # --- Primary: Docling ---
            try:
                logger.info(f"Converting {file_ext} file using Docling: {os.path.basename(file_path)}")
                result = self.get_converter().convert(file_path)
                markdown_content = result.document.export_to_markdown()
                logger.info(f"Successfully converted {os.path.basename(file_path)} to markdown")
                self._save_cache(file_path, markdown_content, result.document)
                return (markdown_content, result.document)
            except Exception as e:
                logger.warning(f"Docling failed for {os.path.basename(file_path)}: {e} — trying PyMuPDF fallback")

            # --- Fallback: PyMuPDF text extraction + RapidOCR for scanned pages ---
            if file_ext == '.pdf':
                try:
                    import fitz  # pymupdf
                    doc = fitz.open(file_path)
                    pages = []
                    scanned_pages = 0
                    for page in doc:
                        text = page.get_text().strip()
                        if text:
                            pages.append(text)
                        else:
                            scanned_pages += 1
                            try:
                                from rapidocr_onnxruntime import RapidOCR
                                if self._rapidocr_reader is None:
                                    logger.info("Initialising RapidOCR reader...")
                                    self._rapidocr_reader = RapidOCR()
                                pix = page.get_pixmap(dpi=200)
                                img_bytes = pix.tobytes("png")
                                ocr_result, _ = self._rapidocr_reader(img_bytes)
                                ocr_text = " ".join([line[1] for line in ocr_result]) if ocr_result else ""
                                if ocr_text:
                                    pages.append(ocr_text)
                            except Exception as ocr_err:
                                logger.warning(f"RapidOCR failed on page {page.number} of {os.path.basename(file_path)}: {ocr_err}")
                    doc.close()
                    if pages:
                        content = "\n\n".join(pages)
                        logger.info(
                            f"PyMuPDF/RapidOCR extracted {len(pages)} pages "
                            f"({scanned_pages} scanned) from {os.path.basename(file_path)}"
                        )
                        return (content, None)
                    logger.warning(f"PyMuPDF + RapidOCR found no text in {os.path.basename(file_path)}")
                except Exception as e:
                    logger.warning(f"PyMuPDF fallback failed for {os.path.basename(file_path)}: {e}")

            # --- Last resort: stub record so the file is still searchable by name ---
            filename = os.path.basename(file_path)
            stub = (
                f"# {os.path.splitext(filename)[0]}\n\n"
                f"[extraction_failed]\n\n"
                f"This document ({filename}) could not be automatically extracted. "
                f"The file may be corrupted, password-protected, or an image-only scan "
                f"that requires manual OCR. Please review the original file."
            )
            logger.error(f"All extraction methods failed for {filename} — storing stub record")
            return (stub, None)

        # Text-based formats (read directly)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return (f.read(), None)
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return (f.read(), None)

    def transcribe_audio(self, file_path: str) -> str:
        """Transcribe audio file using Whisper ASR via Docling."""
        try:
            from docling.document_converter import DocumentConverter, AudioFormatOption
            from docling.datamodel.pipeline_options import AsrPipelineOptions
            from docling.datamodel import asr_model_specs
            from docling.datamodel.base_models import InputFormat
            from docling.pipeline.asr_pipeline import AsrPipeline

            audio_path = Path(file_path).resolve()
            logger.info(f"Transcribing audio file using Whisper Turbo: {audio_path.name}")
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            pipeline_options = AsrPipelineOptions()
            pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO

            converter = DocumentConverter(
                format_options={
                    InputFormat.AUDIO: AudioFormatOption(
                        pipeline_cls=AsrPipeline,
                        pipeline_options=pipeline_options,
                    )
                }
            )
            result = converter.convert(audio_path)
            markdown_content = result.document.export_to_markdown()
            logger.info(f"Successfully transcribed {os.path.basename(file_path)}")
            return markdown_content

        except Exception as e:
            logger.error(f"Failed to transcribe {file_path} with Whisper ASR: {e}")
            return f"[Error: Could not transcribe audio file {os.path.basename(file_path)}]"


def extract_title(content: str, file_path: str) -> str:
    """Extract title from document content or filename."""
    lines = content.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return os.path.splitext(os.path.basename(file_path))[0]


def extract_document_metadata(content: str, file_path: str) -> dict:
    """Extract metadata from document content."""
    from datetime import datetime
    metadata = {
        "file_path": file_path,
        "file_size": len(content),
        "ingestion_date": datetime.now().isoformat(),
        "file_mtime": str(os.path.getmtime(file_path))
    }

    if content.startswith('---'):
        try:
            import yaml
            end_marker = content.find('\n---\n', 4)
            if end_marker != -1:
                frontmatter = content[4:end_marker]
                yaml_metadata = yaml.safe_load(frontmatter)
                if isinstance(yaml_metadata, dict):
                    metadata.update(yaml_metadata)
        except ImportError:
            logger.warning("PyYAML not installed, skipping frontmatter extraction")
        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {e}")

    lines = content.split('\n')
    metadata['line_count'] = len(lines)
    metadata['word_count'] = len(content.split())

    if '[extraction_failed]' in content:
        metadata['extraction_failed'] = True

    return metadata
