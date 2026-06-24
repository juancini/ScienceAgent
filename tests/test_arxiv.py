"""
tests/test_arxiv.py
Unit tests for the arXiv search functionality.
"""

from httpx import patch
import pytest
from tools.arxiv import search_arxiv
from unittest.mock import AsyncMock, MagicMock, patch


def _make_xml(entries: list[dict]) -> str:
    """Build a minimal Atom XML string that mimics the real arXiv response.

    Each entry dict may contain: title, summary, id, published, authors (list).
    This keeps individual tests short and declarative.
    """
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
    ]

    for e in entries:
        parts.append("<entry>")
        parts.append(f"<title>{e.get('title', 'No title')}</title>")
        parts.append(f"<summary>{e.get('summary', '')}</summary>")
        parts.append(f"<id>{e.get('id', 'http://arxiv.org/abs/0000.00000')}</id>")
        parts.append(
            f"<published>{e.get('published', '2024-01-01T00:00:00Z')}</published>"
        )
        for author in e.get("authors", []):
            parts.append(f"<author><name>{author}</name></author>")
        parts.append("</entry>")

    parts.append("</feed>")
    return "\n".join(parts)


def _mock_response(xml_text: str, status_code: int = 200) -> MagicMock:
    """Return a MagicMock that looks like an httpx.Response.

    .raise_for_status() is a no-op for 2xx and raises for 4xx/5xx.
    """
    mock = MagicMock()
    mock.text = xml_text
    mock.status_code = status_code

    if status_code >= 400:
        # Make raise_for_status actually raise, just like httpx does
        import httpx

        mock.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=mock,
        )
    else:
        mock.raise_for_status.return_value = None  # no-op for success

    return mock


class TestTextHelper:
    """_text is a helper function that extracts text from an XML element."""

    def test_text_extraction(self):
        import xml.etree.ElementTree as ET
        from tools.arxiv import _text

        # Create a sample XML element
        xml_str = """
        <entry xmlns="http://www.w3.org/2005/Atom">
            <title>Sample Title</title>
            <summary>Sample Summary</summary>
            <id>http://arxiv.org/abs/1234.5678</id>
            <published>2023-01-01T00:00:00Z</published>
            <author><name>Author One</name></author>
            <author><name>Author Two</name></author>
        </entry>
        """
        element = ET.fromstring(xml_str)

        # Test title extraction
        assert _text(element, "atom:title") == "Sample Title"
        # Test summary extraction
        assert _text(element, "atom:summary") == "Sample Summary"
        # Test id extraction
        assert _text(element, "atom:id") == "http://arxiv.org/abs/1234.5678"
        # Test published extraction
        assert _text(element, "atom:published") == "2023-01-01T00:00:00Z"

    def test_returns_empty_string_for_missing_tag(self):
        import xml.etree.ElementTree as ET
        from tools.arxiv import _text

        # Create a sample XML element without a summary
        xml_str = """
        <entry xmlns="http://www.w3.org/2005/Atom">
            <title>Sample Title</title>
            <id>http://arxiv.org/abs/1234.5678</id>
            <published>2023-01-01T00:00:00Z</published>
            <author><name>Author One</name></author>
            <author><name>Author Two</name></author>
        </entry>
        """
        element = ET.fromstring(xml_str)

        # Test that _text returns an empty string for the missing summary tag
        assert _text(element, "atom:summary") == ""

    def test_tag_exists_but_is_empty(self):
        import xml.etree.ElementTree as ET
        from tools.arxiv import _text

        # Create a sample XML element with an empty summary
        xml_str = """
        <entry xmlns="http://www.w3.org/2005/Atom">
            <title>Sample Title</title>
            <summary></summary>
            <id>http://arxiv.org/abs/1234.5678</id>
            <published>2023-01-01T00:00:00Z</published>
            <author><name>Author One</name></author>
            <author><name>Author Two</name></author>
        </entry>
        """
        element = ET.fromstring(xml_str)

        # Test that _text returns an empty string for the empty summary tag
        assert _text(element, "atom:summary") == ""

    def test_trim_surrounding_whitespace(self):
        import xml.etree.ElementTree as ET
        from tools.arxiv import _text

        # Create a sample XML element with whitespace in the title
        xml_str = """
        <entry xmlns="http://www.w3.org/2005/Atom">
            <title>   Sample Title   </title>
            <summary>Sample Summary</summary>
            <id>http://arxiv.org/abs/1234.5678</id>
            <published>2023-01-01T00:00:00Z</published>
            <author><name>Author One</name></author>
            <author><name>Author Two</name></author>
        </entry>
        """
        element = ET.fromstring(xml_str)

        # Test that _text trims surrounding whitespace
        assert _text(element, "atom:title") == "Sample Title"


class TestSearchArxiv:
    """Tests for the search_arxiv function."""

    @pytest.mark.asyncio
    async def test_search_arxiv_returns_results(self):
        xml = _make_xml(
            [
                {
                    "title": "Attention Is All You Need",
                    "summary": "We propose the Transformer.",
                    "id": "http://arxiv.org/abs/1706.03762",
                    "published": "2017-06-12T00:00:00Z",
                    "authors": ["Vaswani", "Shazeer", "Parmar"],
                }
            ]
        )

        with patch("tools.arxiv.httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.get = AsyncMock(return_value=_mock_response(xml))

            results = await search_arxiv("transformer", ["attention", "transformer"])

        assert len(results) == 1
        r = results[0]
        assert r.source == "arXiv"
        assert r.title == "Attention Is All You Need"
        assert r.url == "http://arxiv.org/abs/1706.03762"
        assert "2017" in r.snippet
        assert "Vaswani" in r.snippet
        assert r.metadata["year"] == "2017"
        assert r.metadata["authors"] == ["Vaswani", "Shazeer", "Parmar"]

    @pytest.mark.asyncio
    async def test_http_error_raises_exception(self):
        with patch("tools.arxiv.httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.get = AsyncMock(
                return_value=_mock_response("<error>Bad Request</error>", 400)
            )

            with pytest.raises(Exception) as exc_info:
                await search_arxiv("invalid query", ["test"])

            assert "HTTP 400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_response(self):
        xml = _make_xml([])
        with patch("tools.arxiv.httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.get = AsyncMock(return_value=_mock_response(xml))

            results = await search_arxiv("Some Topic", [])
        assert results == []

    @pytest.mark.asyncio
    async def test_newlines_are_stripped_from_title_and_summary(self):
        xml = _make_xml(
            [
                {
                    "title": "Multi\nLine\nTitle",
                    "summary": "Summary\nwith\nnewlines.",
                    "authors": ["Author A"],
                }
            ]
        )

        with patch("tools.arxiv.httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.get = AsyncMock(return_value=_mock_response(xml))

            results = await search_arxiv("Some Topic", [])

        r = results[0]
        assert r.title == "Multi Line Title"
        assert "\n" not in r.title
        assert r.snippet == "Author A (2024): Summary with newlines."
        assert "\n" not in r.snippet

    @pytest.mark.asyncio
    async def test_authors_are_truncated_to_three(self):
        xml = _make_xml(
            [
                {
                    "title": "Attention Is All You Need",
                    "summary": "We propose the Transformer.",
                    "id": "http://arxiv.org/abs/1706.03762",
                    "published": "2017-06-12T00:00:00Z",
                    "authors": ["Vaswani", "Shazeer", "Parmar", "Me", "My mate Tom"],
                }
            ]
        )

        with patch("tools.arxiv.httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.get = AsyncMock(return_value=_mock_response(xml))

            results = await search_arxiv("Some Topic", [])

        r = results[0]
        assert len(r.metadata["authors"]) == 3
        assert r.metadata["authors"] == ["Vaswani", "Shazeer", "Parmar"]

    @pytest.mark.asyncio
    async def test_summary_is_truncated_to_500_chars(self):
        long_summary = "Hello World" * 51
        xml = _make_xml(
            [
                {
                    "title": "Attention Is All You Need",
                    "summary": long_summary,
                    "id": "http://arxiv.org/abs/1706.03762",
                    "published": "2017-06-12T00:00:00Z",
                    "authors": ["Vaswani", "Shazeer", "Parmar", "Me", "My mate Tom"],
                }
            ]
        )

        with patch("tools.arxiv.httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.get = AsyncMock(return_value=_mock_response(xml))

            results = await search_arxiv("Some Topic", [])

        r = results[0]
        summary_part = r.snippet.split(": ", 1)[1]
        assert len(summary_part) <= 500
