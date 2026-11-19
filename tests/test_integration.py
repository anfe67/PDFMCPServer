import pytest
from pathlib import Path
from main import read_pdf, read_pdf_page, get_pdf_info, list_pdfs, upload_pdf, delete_pdf, STORAGE_DIR
import base64


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
        result = read_pdf(sample_pdf)
        assert isinstance(result, str)
        assert "Error" not in result
        assert "Page" in result or "Warning" in result
    
    def test_read_pdf_page_integration(self, sample_pdf):
        """Test read_pdf_page with a real PDF file."""
        result = read_pdf_page(sample_pdf, 1)
        assert isinstance(result, str)
        assert "Error" not in result
        assert "Page 1" in result or "Warning" in result
    
    def test_get_pdf_info_integration(self, sample_pdf):
        """Test get_pdf_info with a real PDF file."""
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
        result = list_pdfs(str(fixtures_dir))
        assert isinstance(result, list)
        assert len(result) > 0
        # Should find at least the sample PDFs we downloaded
        assert any("sample1.pdf" in path for path in result)
        assert all("Error" not in path for path in result)
    
    def test_read_pdf_multiple_samples(self, fixtures_dir):
        """Test read_pdf with multiple sample PDFs."""
        pdf_files = list(fixtures_dir.glob("*.pdf"))
        
        for pdf_path in pdf_files[:3]:  # Test first 3 PDFs
            result = read_pdf(str(pdf_path))
            assert isinstance(result, str)
            # Either successful extraction or warning about no text
            assert "Error reading PDF" not in result
    
    def test_get_pdf_info_multiple_samples(self, fixtures_dir):
        """Test get_pdf_info with multiple sample PDFs."""
        pdf_files = list(fixtures_dir.glob("*.pdf"))
        
        for pdf_path in pdf_files[:3]:  # Test first 3 PDFs
            result = get_pdf_info(str(pdf_path))
            assert isinstance(result, dict)
            assert "error" not in result
            assert result["page_count"] > 0
            assert result["file_size_bytes"] > 0
    
    def test_read_pdf_page_out_of_range(self, sample_pdf):
        """Test read_pdf_page with page number out of range."""
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

    def test_upload_pdf_integration(self, sample_pdf):
        """Test upload_pdf with a real PDF file."""
        with open(sample_pdf, "rb") as f:
            content_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        filename = "uploaded_sample.pdf"
        # Use a clean path in storage
        target_path = STORAGE_DIR / filename
        if target_path.exists():
            target_path.unlink()
            
        result = upload_pdf(filename, content_base64)
        
        assert result == str(target_path.absolute())
        assert target_path.exists()
        assert target_path.stat().st_size > 0
        
        # Verify content
        with open(target_path, "rb") as f:
            assert f.read() == base64.b64decode(content_base64)
            
        # Verify read_pdf works with the uploaded file
        read_result = read_pdf(str(target_path))
        assert isinstance(read_result, str)
        assert "Error" not in read_result
        
        # Clean up
        target_path.unlink()

    def test_delete_pdf_integration(self, sample_pdf):
        """Test delete_pdf with a real PDF file."""
        # First upload a file to delete
        with open(sample_pdf, "rb") as f:
            content_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        filename = "to_be_deleted.pdf"
        target_path = STORAGE_DIR / filename
        if target_path.exists():
            target_path.unlink()
            
        upload_result = upload_pdf(filename, content_base64)
        assert target_path.exists()
        
        # Now delete it
        delete_result = delete_pdf(filename)
        assert "Successfully deleted" in delete_result
        assert not target_path.exists()
        
        # Delete non-existent file
        delete_result_missing = delete_pdf("not_found.pdf")
        assert "Error: File not found" in delete_result_missing

    def test_upload_path_traversal(self):
        """Test that upload_pdf prevents path traversal."""
        with open("dummy.pdf", "w") as f:
            f.write("dummy content")
            
        try:
            with open("dummy.pdf", "rb") as f:
                content_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Attempt traversal
            result = upload_pdf("../evil.pdf", content_base64)
            assert "evil.pdf" in result
            assert not Path("/evil.pdf").exists()
            assert not Path("../../evil.pdf").exists()
            
            # Verify file ended up in storage dir with safe name
            stored_path = STORAGE_DIR / "evil.pdf"
            assert stored_path.exists()
            assert not stored_path.parent != STORAGE_DIR
            
            stored_path.unlink()
        finally:
            Path("dummy.pdf").unlink()

    def test_list_pdfs_defaults_to_storage(self):
        """Test list_pdfs with no arguments lists storage directory."""
        # Put a dummy file in storage
        test_file = STORAGE_DIR / "test_default.pdf"
        test_file.write_text("fake pdf content")
        
        try:
            results = list_pdfs()
            assert any("test_default.pdf" in p for p in results)
            assert all(Path(p).resolve().parent == STORAGE_DIR.resolve() for p in results)
        finally:
            test_file.unlink()

    def test_upload_non_pdf(self):
        """Test upload_pdf rejects non-pdf files."""
        content_base64 = base64.b64encode(b"not a pdf").decode("utf-8")
        result = upload_pdf("malicious.exe", content_base64)
        assert "must end in .pdf" in result
