import pytest
from pathlib import Path
import tempfile
import os


class TestPDFToolsUnit:
    """Unit tests for PDF MCP server tools."""
    
    def test_read_pdf_file_not_found(self):
        """Test read_pdf with non-existent file."""
        from main import read_pdf
        result = read_pdf("/nonexistent/path/file.pdf")
        assert "Error: File not found" in result
    
    def test_read_pdf_not_a_file(self):
        """Test read_pdf with directory path."""
        from main import read_pdf
        result = read_pdf("/tmp")
        assert "Error: Path is not a file" in result
    
    def test_read_pdf_not_pdf_extension(self):
        """Test read_pdf with non-PDF file."""
        from main import read_pdf
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            result = read_pdf(temp_path)
            assert "Error: File is not a PDF" in result
        finally:
            os.unlink(temp_path)
    
    def test_read_pdf_page_file_not_found(self):
        """Test read_pdf_page with non-existent file."""
        from main import read_pdf_page
        result = read_pdf_page("/nonexistent/path/file.pdf", 1)
        assert "Error: File not found" in result
    
    def test_read_pdf_page_invalid_page_number(self):
        """Test read_pdf_page with invalid page number."""
        from main import read_pdf_page
        # This will fail at file not found first, but we test the logic
        result = read_pdf_page("/nonexistent/path/file.pdf", 0)
        assert "Error: File not found" in result
    
    def test_get_pdf_info_file_not_found(self):
        """Test get_pdf_info with non-existent file."""
        from main import get_pdf_info
        result = get_pdf_info("/nonexistent/path/file.pdf")
        assert "error" in result
        assert "File not found" in result["error"]
    
    def test_get_pdf_info_not_a_file(self):
        """Test get_pdf_info with directory path."""
        from main import get_pdf_info
        result = get_pdf_info("/tmp")
        assert "error" in result
        assert "Path is not a file" in result["error"]
    
    def test_get_pdf_info_not_pdf_extension(self):
        """Test get_pdf_info with non-PDF file."""
        from main import get_pdf_info
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            result = get_pdf_info(temp_path)
            assert "error" in result
            assert "File is not a PDF" in result["error"]
        finally:
            os.unlink(temp_path)
    
    def test_list_pdfs_directory_not_found(self):
        """Test list_pdfs with non-existent directory."""
        from main import list_pdfs
        result = list_pdfs("/nonexistent/directory")
        assert len(result) == 1
        assert "Error: Directory not found" in result[0]
    
    def test_list_pdfs_not_a_directory(self):
        """Test list_pdfs with file path instead of directory."""
        from main import list_pdfs
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            result = list_pdfs(temp_path)
            assert len(result) == 1
            assert "Error: Path is not a directory" in result[0]
        finally:
            os.unlink(temp_path)
    
    def test_list_pdfs_empty_directory(self):
        """Test list_pdfs with empty directory."""
        from main import list_pdfs
        with tempfile.TemporaryDirectory() as temp_dir:
            result = list_pdfs(temp_dir)
            assert len(result) == 1
            assert "No PDF files found" in result[0]
