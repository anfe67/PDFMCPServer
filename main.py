import os
import base64
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from pypdf import PdfReader
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Configure storage directory with environment variable support
STORAGE_DIR = Path(os.getenv("PDF_STORAGE_DIR", "/data/pdfs"))

# Attempt to create the directory, but handle permission errors gracefully
try:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fall back to local storage if /data is not writable
    STORAGE_DIR = Path("storage/pdfs")
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Warning: Using local storage directory instead of {os.getenv('PDF_STORAGE_DIR', '/data/pdfs')}")
    print(f"Storage directory: {STORAGE_DIR.absolute()}")

mcp = FastMCP("PDF Reader")

# Expose the storage directory as a resource so clients know where it is
@mcp.resource("mcp://pdf-server/pdfs/")
def get_pdf_storage_info() -> str:
    """Returns information about the PDF storage directory."""
    return f"PDF storage directory: {STORAGE_DIR}\nAvailable files: " + ", ".join(
        (p.name for p in STORAGE_DIR.glob("*.pdf"))
    )

@mcp.resource("mcp://pdf-server/pdfs/{filename}")
def read_pdf_resource(filename: str) -> str:
    """Provides PDF content as a resource."""
    path = STORAGE_DIR / filename
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise ValueError("File not found or not a PDF")
    return path.read_text(encoding="utf-8", errors="ignore")

# Configure CORS middleware for browser-based clients
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=[
            "mcp-protocol-version",
            "mcp-session-id",
            "mcp-method",
            "mcp-name",
            "Authorization",
            "Content-Type",
        ],
        expose_headers=["mcp-session-id"],
    )
]

@mcp.tool()
def upload_pdf(filename: str, content_base64: str) -> str:
    """
    Upload a PDF file to the container's PDF storage directory.
    
    This is the primary way for clients to send files to the server
    when running in a container.
    
    Args:
        filename: The desired filename (must end in .pdf)
        content_base64: Base64 encoded PDF file content
        
    Returns:
        The absolute path to the stored file, or an error message
    """
    if not filename.lower().endswith(".pdf"):
        return "Error: filename must end in .pdf"
    
    # Prevent path traversal
    safe_filename = os.path.basename(filename)
    target_path = STORAGE_DIR / safe_filename
    
    try:
        content = base64.b64decode(content_base64)
        with open(target_path, "wb") as f:
            f.write(content)
        
        # Set permissions so the server can read/write
        target_path.chmod(0o666)
        
        return target_path.absolute().as_posix()
    except Exception as e:
        return f"Error uploading PDF: {str(e)}"

@mcp.tool()
def delete_pdf(filename: str) -> str:
    """
    Remove a PDF from the storage directory.
    
    Args:
        filename: The name of the file to delete
    """
    if not filename or not filename.strip():
        return f"Error: File not found"
    
    safe_filename = os.path.basename(filename)
    target_path = STORAGE_DIR / safe_filename
    
    if not target_path.exists():
        return f"Error: File not found"
    
    try:
        target_path.unlink()
        return f"Successfully deleted {filename}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@mcp.tool()
def read_pdf(file_path: Optional[str] = None) -> str:
    """Read a PDF file and extract all text content.
    
    If file_path is not provided, it searches the default storage directory.
    
    Args:
        file_path: Path to the PDF file (defaults to searching /data/pdfs)
    """
    if file_path is None:
        # Search for PDFs in storage directory
        pdf_files = list(STORAGE_DIR.glob("*.pdf"))
        pdf_files.extend(STORAGE_DIR.glob("*.PDF"))
        
        if not pdf_files:
            return f"Error: No PDF files found in {STORAGE_DIR}"
        
        if len(pdf_files) > 1:
            return f"Error: Multiple PDF files found in {STORAGE_DIR}. Please specify a file."
        
        path = pdf_files[0]
    else:
        path = Path(file_path)
    
    if not path.exists():
        return f"Error: File not found at {file_path}"
    
    if not path.is_file():
        return f"Error: Path is not a file: {file_path}"
    
    if path.suffix.lower() != '.pdf':
        return f"Error: File is not a PDF: {file_path}"
    
    try:
        reader = PdfReader(str(path))
        text_content = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text.strip():
                text_content.append(f"--- Page {page_num} ---\n{page_text}")
        
        if not text_content:
            return "Warning: No text content found in PDF (may be image-based or empty)"
        
        return "\n\n".join(text_content)
    
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

@mcp.tool()
def read_pdf_page(file_path: str, page_number: int) -> str:
    """Read a specific page from a PDF file.
    
    Args:
        file_path: Absolute or relative path to the PDF file
        page_number: 1-based page number to read
        
    Returns:
        Extracted text from the specified page, or error message
    """
    path = Path(file_path)
    
    if not path.exists():
        return f"Error: File not found at {file_path}"
    
    if not path.is_file():
        return f"Error: Path is not a file: {file_path}"
    
    if path.suffix.lower() != '.pdf':
        return f"Error: File is not a PDF: {file_path}"
    
    try:
        reader = PdfReader(file_path)
        
        if page_number < 1 or page_number > len(reader.pages):
            return f"Error: Page number {page_number} is out of range. PDF has {len(reader.pages)} pages."
        
        page = reader.pages[page_number - 1]
        page_text = page.extract_text()
        
        if not page_text or not page_text.strip():
            return f"Warning: No text content found on page {page_number} (may be image-based or empty)"
        
        return f"--- Page {page_number} ---\n{page_text}"
    
    except Exception as e:
        return f"Error reading PDF page: {str(e)}"

@mcp.tool()
def get_pdf_info(file_path: Optional[str] = None) -> dict:
    """Get metadata and information about a PDF file.
    
    Args:
        file_path: Absolute or relative path to the PDF file. If None, searches storage directory.
        
    Returns:
        Dictionary with PDF metadata including page count, metadata, and file info
    """
    if file_path is None:
        # Search for PDFs in storage directory
        pdf_files = list(STORAGE_DIR.glob("*.pdf"))
        pdf_files.extend(STORAGE_DIR.glob("*.PDF"))
        
        if not pdf_files:
            return {"error": f"No PDF files found in {STORAGE_DIR}"}
        
        if len(pdf_files) > 1:
            return {"error": f"Multiple PDF files found in {STORAGE_DIR}. Please specify a file."}
        
        path = pdf_files[0]
    else:
        path = Path(file_path)
    
    if not path.exists():
        return {"error": f"File not found at {file_path}"}
    
    if not path.is_file():
        return {"error": f"Path is not a file: {file_path}"}
    
    if path.suffix.lower() != '.pdf':
        return {"error": f"File is not a PDF: {file_path}"}
    
    try:
        reader = PdfReader(str(path))
        
        info = {
            "page_count": len(reader.pages),
            "file_path": str(path.absolute()),
            "file_size_bytes": path.stat().st_size,
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "metadata": reader.metadata or {},
            "is_encrypted": reader.is_encrypted,
        }
        
        # Clean up metadata (remove None values and decode bytes)
        cleaned_metadata = {}
        if info["metadata"]:
            for key, value in info["metadata"].items():
                if value is not None:
                    if isinstance(value, bytes):
                        try:
                            cleaned_metadata[key] = value.decode('utf-8', errors='ignore')
                        except:
                            cleaned_metadata[key] = str(value)
                    else:
                        cleaned_metadata[key] = str(value)
        
        info["metadata"] = cleaned_metadata
        
        return info
    
    except Exception as e:
        return {"error": f"Error reading PDF info: {str(e)}"}

@mcp.tool()
def list_pdfs(directory: Optional[str] = None) -> list[str]:
    """List all PDF files in a directory.
    
    Defaults to the container's storage directory if no directory is specified.
    
    Args:
        directory: Absolute or relative path to the directory
    
    Returns:
        List of PDF file paths found in the directory
    """
    path = Path(directory or STORAGE_DIR)
    
    if not path.exists():
        return [f"Error: Directory not found at {directory}"]
    
    if not path.is_dir():
        return [f"Error: Path is not a directory: {directory}"]
    
    try:
        pdf_files = list(path.glob("*.pdf"))
        pdf_files.extend(path.glob("*.PDF"))
        
        if not pdf_files:
            return [f"No PDF files found in {directory}"]
        
        return [str(pdf.absolute()) for pdf in sorted(pdf_files)]
    
    except Exception as e:
        return [f"Error listing PDFs: {str(e)}"]

if __name__ == "__main__":
    # Exposes HTTP at http://0.0.0.0:8001/mcp
    mcp.run(transport="http", host="0.0.0.0", port=8001, middleware=middleware)