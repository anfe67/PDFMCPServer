from fastmcp import FastMCP
from pypdf import PdfReader
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import os

mcp = FastMCP("PDF Reader")

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
def read_pdf(file_path: str) -> str:
    """Read a PDF file and extract all text content.
    
    Args:
        file_path: Absolute or relative path to the PDF file
        
    Returns:
        Extracted text content from all pages, or error message if file cannot be read
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
def get_pdf_info(file_path: str) -> dict:
    """Get metadata and information about a PDF file.
    
    Args:
        file_path: Absolute or relative path to the PDF file
        
    Returns:
        Dictionary with PDF metadata including page count, metadata, and file info
    """
    path = Path(file_path)
    
    if not path.exists():
        return {"error": f"File not found at {file_path}"}
    
    if not path.is_file():
        return {"error": f"Path is not a file: {file_path}"}
    
    if path.suffix.lower() != '.pdf':
        return {"error": f"File is not a PDF: {file_path}"}
    
    try:
        reader = PdfReader(file_path)
        
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
def list_pdfs(directory: str) -> list[str]:
    """List all PDF files in a directory.
    
    Args:
        directory: Absolute or relative path to the directory
        
    Returns:
        List of PDF file paths found in the directory
    """
    path = Path(directory)
    
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
