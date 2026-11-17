import pytest
from pathlib import Path


class TestPDFToolsIntegration:
    """Integration tests for PDF MCP server tools using real PDF files."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"
    
    @pytest.fixture
    def sample_pdf(self, fixtures_dir):
        """Get a sample PDF file path."""
        pdf_path = fixtures_dir / "sample1.pdf"
        assert pdf_path.exists(), f"Sample PDF not found at {pdf_path}"
        return str(pdf_path)
    
    def test_read_pdf_integration(self, sample_pdf):
        """Test read_pdf with a real PDF file."""
        from main import read_pdf
        result = read_pdf(sample_pdf)
        assert isinstance(result, str)
        assert "Error" not in result
        assert "Page" in result or "Warning" in result
    
    def test_read_pdf_page_integration(self, sample_pdf):
        """Test read_pdf_page with a real PDF file."""
        from main import read_pdf_page
        result = read_pdf_page(sample_pdf, 1)
        assert isinstance(result, str)
        assert "Error" not in result
        assert "Page 1" in result or "Warning" in result
    
    def test_get_pdf_info_integration(self, sample_pdf):
        """Test get_pdf_info with a real PDF file."""
        from main import get_pdf_info
        result = get_pdf_info(sample_pdf)
        assert isinstance(result, dict)
        assert "error" not in result
        assert "page_count" in result
        assert "file_path" in result
        assert "file_size_bytes" in result
        assert "file_size_mb" in result
        assert "is_encrypted" in result
        assert "metadata" in result
        assert result["page_count"] > 0
        assert result["file_size_bytes"] > 0
    
    def test_list_pdfs_integration(self, fixtures_dir):
        """Test list_pdfs with real PDF files in fixtures directory."""
        from main import list_pdfs
        result = list_pdfs(str(fixtures_dir))
        assert isinstance(result, list)
        assert len(result) > 0
        # Should find at least the sample PDFs we downloaded
        assert any("sample1.pdf" in path for path in result)
        assert all("Error" not in path for path in result)
    
    def test_read_pdf_multiple_samples(self, fixtures_dir):
        """Test read_pdf with multiple sample PDFs."""
        from main import read_pdf
        pdf_files = list(fixtures_dir.glob("*.pdf"))
        
        for pdf_path in pdf_files[:3]:  # Test first 3 PDFs
            result = read_pdf(str(pdf_path))
            assert isinstance(result, str)
            # Either successful extraction or warning about no text
            assert "Error reading PDF" not in result
    
    def test_get_pdf_info_multiple_samples(self, fixtures_dir):
        """Test get_pdf_info with multiple sample PDFs."""
        from main import get_pdf_info
        pdf_files = list(fixtures_dir.glob("*.pdf"))
        
        for pdf_path in pdf_files[:3]:  # Test first 3 PDFs
            result = get_pdf_info(str(pdf_path))
            assert isinstance(result, dict)
            assert "error" not in result
            assert result["page_count"] > 0
            assert result["file_size_bytes"] > 0
    
    def test_read_pdf_page_out_of_range(self, sample_pdf):
        """Test read_pdf_page with page number out of range."""
        from main import read_pdf_page
        from main import get_pdf_info
        
        # First get the page count
        info = get_pdf_info(sample_pdf)
        page_count = info["page_count"]
        
        # Try to read a page beyond the count
        result = read_pdf_page(sample_pdf, page_count + 1)
        assert "Error" in result
        assert "out of range" in result
    
    def test_read_pdf_page_negative(self, sample_pdf):
        """Test read_pdf_page with negative page number."""
        from main import read_pdf_page
        result = read_pdf_page(sample_pdf, -1)
        assert "Error" in result
        assert "out of range" in result
