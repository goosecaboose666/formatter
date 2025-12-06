import os
import pytest
from app.services.scrubber import DocumentScrubber

# Define paths to sample files
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
TXT_FILE = os.path.join(TEST_FILES_DIR, "sample.txt")
HTML_FILE = os.path.join(TEST_FILES_DIR, "sample.html")

@pytest.fixture
def scrubber():
    return DocumentScrubber()

def test_scrub_txt_file(scrubber):
    result = scrubber.process_file(TXT_FILE, "txt")

    assert "simple text file" in result
    assert "https://example.com" not in result
    assert "[LINK_REMOVED]" in result
    assert "contact@spam-me.com" not in result
    assert "[EMAIL_REMOVED]" in result
    # Check whitespace cleaning (single space between 'extra' and 'whitespace')
    assert "extra whitespace" in result

def test_scrub_html_file(scrubber):
    result = scrubber.process_file(HTML_FILE, "html")

    # Title and head should be gone
    assert "Ignore Me" not in result
    # Header should be there
    assert "Header Content" in result
    # Script should be gone
    assert "console.log" not in result
    assert "ad script" not in result
    # Links should be scrubbed
    assert "http://ad.com" not in result
    assert "[LINK_REMOVED]" in result

def test_scrubber_cleaning_logic(scrubber):
    raw_text = "Bad   Spacing. \n\n\n Too many lines. \n email@test.com"
    clean_text = scrubber._scrub_text(raw_text)

    assert "Bad Spacing." in clean_text
    assert "\n\n" in clean_text
    assert "\n\n\n" not in clean_text
    assert "[EMAIL_REMOVED]" in clean_text
