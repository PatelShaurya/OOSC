"""
Document loader module using PyMuPDF (fitz) for PDF text extraction.
"""
from pathlib import Path
from typing import List, Tuple, Union
import pymupdf as fitz  # PyMuPDF


class DocumentLoaderError(Exception):
    """Custom exception for document loading errors."""
    pass


class DocumentLoader:
    """Handles loading and page-by-page text extraction from PDF files."""

    @staticmethod
    def load_pdf(pdf_path: Union[str, Path]) -> List[Tuple[int, str]]:
        """
        Loads a PDF file and extracts text page-by-page.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of tuples (page_number [1-indexed], raw_text).

        Raises:
            FileNotFoundError: If the file does not exist.
            DocumentLoaderError: If file is not a PDF or cannot be parsed.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at: {path}")

        if not path.is_file():
            raise DocumentLoaderError(f"Specified path is not a file: {path}")

        if path.suffix.lower() != ".pdf":
            raise DocumentLoaderError(f"File is not a PDF: {path}")

        pages: List[Tuple[int, str]] = []
        try:
            doc = fitz.open(path)
            if doc.is_encrypted:
                raise DocumentLoaderError(f"PDF file is encrypted: {path}")

            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                text = page.get_text("text")
                pages.append((page_index + 1, text))

            doc.close()
        except fitz.FileDataError as e:
            raise DocumentLoaderError(f"Failed to parse PDF file {path}: {str(e)}") from e
        except Exception as e:
            if isinstance(e, (FileNotFoundError, DocumentLoaderError)):
                raise e
            raise DocumentLoaderError(f"Error reading PDF file {path}: {str(e)}") from e

        return pages
