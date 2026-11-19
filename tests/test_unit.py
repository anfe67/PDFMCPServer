import pytest
from pathlib import Path
import tempfile
import os
import base64
from main import (
    read_pdf, 
    read_pdf_page, 
    get_pdf_info, 
    list_pdfs, 
    upload_pdf, 
    delete_pdf, 
    STORAGE_DIR
)


class TestPDFToolsUnit:
    """Unit tests for PDF MCP server tools."""
    
    # --- Existing tests ---

    def test_read_pdf_file_not_found(self):
        """Test read_pdf with non-existent file."""
        result = read_pdf("/nonexistent/path/file.pdf")
        assert "Error: File not found" in result
    
    def test_read_pdf_not_a_file(self):
        """Test read_pdf with directory path."""
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

    # --- New tests for the storage system ---

    def test_upload_pdf_invalid_filename(self):
        """Test upload_pdf rejects filenames without .pdf extension."""
        content_base64 = base64.b64encode(b"fake pdf content").decode("utf-8")
        result = upload_pdf("malicious.exe", content_base64)
        assert "must end in .pdf" in result

    def test_upload_pdf_empty_content(self):
        """Test upload_pdf with empty base64 content."""
        result = upload_pdf("empty.pdf", "")
        # pypdf will probably complain, but upload_pdf should still attempt it
        # and return either the path or a base64 decoding error
        assert "Error" in result or "/data/pdfs/empty.pdf" in result or "storage/pdfs/empty.pdf" in result

    def test_upload_pdf_invalid_base64(self):
        """Test upload_pdf with invalid base64 encoding."""
        result = upload_pdf("invalid.pdf", "not-base64-content!!!")
        # base64.b64decode doesn't raise exceptions for invalid input, it decodes what it can
        # So the file is still written. Clean it up.
        if "Error" not in result:
            Path(result).unlink()
        # The test verifies the function handles the input without crashing

    def test_delete_pdf_nonexistent(self):
        """Test delete_pdf with a filename that doesn't exist."""
        result = delete_pdf("never-existed.pdf")
        assert "Error: File not found" in result

    def test_read_pdf_defaults_to_storage(self):
        """Test read_pdf with no arguments uses the default storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with tempfile.NamedTemporaryFile(suffix=".pdf", dir=temp_dir, delete=False) as f:
                f.write(b"%PDF-1.4 fake content")
                temp_pdf = f.name
            
            try:
                # Temporarily patch STORAGE_DIR for this test
                original_storage = STORAGE_DIR
                try:
                    import main
                    main.STORAGE_DIR = Path(temp_dir)
                    from main import read_pdf
                    result = read_pdf()  # uses default directory
                    assert isinstance(result, str)
                    # Should either succeed, warn about no text content, or fail to parse fake PDF
                    assert "Error" not in result or "No text content" in result or "Error reading PDF" in result
                finally:
                    main.STORAGE_DIR = original_storage
            finally:
                os.unlink(temp_pdf)

    def test_get_pdf_info_defaults_to_storage(self):
        """Test get_pdf_info with no arguments uses the default storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with tempfile.NamedTemporaryFile(suffix=".pdf", dir=temp_dir, delete=False) as f:
                f.write(b"%PDF-1.4 fake content")
                temp_pdf = f.name
            
            try:
                # Temporarily patch STORAGE_DIR
                original_storage = STORAGE_DIR
                try:
                    import main
                    main.STORAGE_DIR = Path(temp_dir)
                    from main import get_pdf_info
                    # Pass None to trigger default directory behavior
                    result = get_pdf_info(None)
                    assert isinstance(result, dict)
                    # With a fake PDF, it might have an error, but the function should handle it
                    assert "error" not in result or "PDF" in result["error"]
                finally:
                    main.STORAGE_DIR = original_storage
            finally:
                os.unlink(temp_pdf)

    def test_list_pdfs_defaults_to_storage(self):
        """Test list_pdfs with no arguments uses the default storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy PDF
            pdf_file = Path(temp_dir) / "test.pdf"
            pdf_file.write_text("%PDF-1.4 fake content")
            
            # Temporarily patch STORAGE_DIR
            original_storage = STORAGE_DIR
            try:
                import main
                main.STORAGE_DIR = Path(temp_dir)
                from main import list_pdfs
                result = list_pdfs()  # uses default directory
                assert len(result) == 1
                assert pdf_file.name in result[0]
            finally:
                main.STORAGE_DIR = original_storage

    def test_get_pdf_info_nonexistent(self):
        """Test get_pdf_info with a nonexistent file."""
        result = get_pdf_info("/tmp/nonexistent_file_12345.pdf")
        assert "error" in result
        assert "File not found" in result["error"]

    def test_delete_pdf_invalid_filename(self):
        """Test delete_pdf with empty filename."""
        result = delete_pdf("")
        assert "Error: File not found" in result

    def test_upload_pdf_path_traversal_logic(self):
        """Test that upload_pdf uses only the basename of the filename."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"fake content")
            temp_path = f.name
        
        try:
            # The test verifies that upload_pdf uses only the basename of the filename
            # to prevent path traversal attacks
            result = upload_pdf("../evil.pdf", base64.b64encode(b"fake content").decode("utf-8"))
            assert "evil.pdf" in result
            assert not Path("/evil.pdf").exists()
            assert not Path("../../evil.pdf").exists()
            
            # Verify file ended up in storage dir with safe name
            stored_path = STORAGE_DIR / "evil.pdf"
            assert stored_path.exists()
            assert not stored_path.parent != STORAGE_DIR
            
            stored_path.unlink()
        finally:
            Path(temp_path).unlink()
