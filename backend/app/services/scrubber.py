import re
from typing import Optional
from pathlib import Path
import logging

# Libraries for different file types
from unstructured.partition.auto import partition
from unstructured.cleaners.core import clean, clean_bullets, group_broken_paragraphs
import pypdf
import docx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DocumentScrubber:
    """
    Handles extracting text from various file formats and scrubbing it
    using deterministic rules (no AI).
    """

    def process_file(self, file_path: str, file_type: str) -> str:
        """
        Main entry point for processing a file.
        Detects type if not provided (though file_type arg is preferred)
        and dispatches to the correct extractor, then cleans the output.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        raw_text = ""

        # Dispatch based on extension or provided type
        ext = path.suffix.lower()

        try:
            if ext == ".pdf":
                raw_text = self._extract_pdf(path)
            elif ext == ".docx":
                raw_text = self._extract_docx(path)
            elif ext in [".html", ".htm"]:
                raw_text = self._extract_html(path)
            elif ext in [".txt", ".md", ".csv"]:
                raw_text = path.read_text(encoding="utf-8")
            else:
                # Fallback to unstructured auto-partition
                logger.info(f"Using generic unstructured partition for {file_path}")
                elements = partition(filename=str(path))
                raw_text = "\n\n".join([str(e) for e in elements])

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise ValueError(f"Failed to process file {file_path}: {str(e)}")

        return self._scrub_text(raw_text)

    def _extract_pdf(self, path: Path) -> str:
        text = []
        try:
            reader = pypdf.PdfReader(path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        except Exception as e:
            logger.warning(f"PyPDF2 failed, falling back to unstructured for {path}: {e}")
            elements = partition(filename=str(path))
            return "\n\n".join([str(e) for e in elements])

        return "\n\n".join(text)

    def _extract_docx(self, path: Path) -> str:
        doc = docx.Document(path)
        return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    def _extract_html(self, path: Path) -> str:
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "head", "title", "meta", "[document]"]):
                script.extract()

            text = soup.get_text(separator="\n\n")
            return text

    def _scrub_text(self, text: str) -> str:
        """
        Applies a series of cleaning rules to the raw text.
        """
        if not text:
            return ""

        # 1. Custom Regex Cleaning - Apply mostly BEFORE whitespace merging to match patterns reliable

        # Remove emails (privacy/noise)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '[EMAIL_REMOVED]', text)

        # Remove URLs
        url_pattern = r'https?://\S+|www\.\S+'
        text = re.sub(url_pattern, '[LINK_REMOVED]', text)

        # 2. Use unstructured cleaners (but selective)
        # clean_bullets removes bullets but keeps text
        text = clean_bullets(text)

        # group_broken_paragraphs tries to merge lines that look like they belong together
        # (e.g. lines ending without punctuation)
        text = group_broken_paragraphs(text)

        # 3. Normalize Whitespace manually to preserve paragraphs
        # Replace non-breaking spaces
        text = text.replace('\xa0', ' ')

        # Split into lines, strip each line, and rejoin
        lines = [line.strip() for line in text.splitlines()]

        # Remove empty lines, but keep paragraph structure?
        # A simple strategy: join with newlines, then replace 3+ newlines with 2.
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Collapse multiple spaces within a line
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()
