"""PDF parser for credit card statements.

Handles PDF decryption with pikepdf and text extraction with pdfplumber.
"""

import io
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
import pikepdf


class PdfDecryptionError(Exception):
    """Raised when PDF decryption fails."""

    pass


class PdfParseError(Exception):
    """Raised when PDF text extraction fails."""

    pass


@dataclass
class PdfPage:
    """Represents a page of extracted text from a PDF."""

    page_number: int
    text: str
    tables: list[list[list[str]]]


@dataclass
class PdfContent:
    """Represents extracted content from a PDF."""

    pages: list[PdfPage]
    total_pages: int

    @property
    def full_text(self) -> str:
        """Get all text concatenated from all pages."""
        return "\n\n".join(page.text for page in self.pages)

    @property
    def all_tables(self) -> list[list[list[str]]]:
        """Get all tables from all pages."""
        tables = []
        for page in self.pages:
            tables.extend(page.tables)
        return tables


class PdfParser:
    """Parser for credit card statement PDFs.

    Handles decryption of password-protected PDFs and extracts text/tables.
    """

    def __init__(self, pdf_data: bytes):
        """Initialize with PDF data.

        Args:
            pdf_data: Raw PDF file bytes.
        """
        self._pdf_data = pdf_data
        self._decrypted_data: bytes | None = None

    def is_encrypted(self) -> bool:
        """Check if the PDF is password-protected."""
        try:
            with io.BytesIO(self._pdf_data) as f:
                pdf = pikepdf.open(f)
                pdf.close()
                return False
        except pikepdf.PasswordError:
            return True
        except Exception:
            # Other errors might indicate corruption, treat as not encrypted
            return False

    def decrypt(self, password: str) -> None:
        """Decrypt the PDF with the given password.

        Args:
            password: The PDF password.

        Raises:
            PdfDecryptionError: If decryption fails.
        """
        try:
            with io.BytesIO(self._pdf_data) as f:
                pdf = pikepdf.open(f, password=password)

                # Save decrypted PDF to bytes
                output = io.BytesIO()
                pdf.save(output)
                self._decrypted_data = output.getvalue()
                pdf.close()
        except pikepdf.PasswordError as e:
            raise PdfDecryptionError(f"Invalid password: {e}")
        except Exception as e:
            raise PdfDecryptionError(f"Failed to decrypt PDF: {e}")

    def extract_text(self) -> PdfContent:
        """Extract text and tables from the PDF.

        Returns:
            PdfContent with extracted text and tables.

        Raises:
            PdfParseError: If text extraction fails.
        """
        data = self._decrypted_data if self._decrypted_data else self._pdf_data

        try:
            pages = []
            with io.BytesIO(data) as f, pdfplumber.open(f) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Extract text
                    text = page.extract_text() or ""

                    # Extract tables
                    tables = []
                    for table in page.extract_tables():
                        if table:
                            # Convert None cells to empty strings
                            cleaned_table = [
                                [cell if cell is not None else "" for cell in row] for row in table
                            ]
                            tables.append(cleaned_table)

                    pages.append(PdfPage(page_number=i + 1, text=text, tables=tables))

                return PdfContent(pages=pages, total_pages=len(pdf.pages))
        except Exception as e:
            raise PdfParseError(f"Failed to extract text from PDF: {e}")

    @classmethod
    def from_file(cls, file_path: str | Path) -> "PdfParser":
        """Create a PdfParser from a file path.

        Args:
            file_path: Path to the PDF file.

        Returns:
            PdfParser instance.
        """
        with open(file_path, "rb") as f:
            return cls(f.read())

    def save_decrypted(self, output_path: str | Path) -> None:
        """Save the decrypted PDF to a file.

        Args:
            output_path: Path to save the decrypted PDF.

        Raises:
            ValueError: If PDF hasn't been decrypted.
        """
        if not self._decrypted_data:
            raise ValueError("PDF hasn't been decrypted yet")

        with open(output_path, "wb") as f:
            f.write(self._decrypted_data)

    def get_decrypted_bytes(self) -> bytes:
        """Get the decrypted PDF bytes.

        Returns:
            Decrypted PDF data, or original data if not encrypted.
        """
        return self._decrypted_data if self._decrypted_data else self._pdf_data


def decrypt_and_extract(pdf_data: bytes, password: str | None = None) -> tuple[PdfContent, bool]:
    """Convenience function to decrypt and extract PDF content.

    Args:
        pdf_data: Raw PDF bytes.
        password: Optional password for encrypted PDFs.

    Returns:
        Tuple of (PdfContent, was_encrypted).

    Raises:
        PdfDecryptionError: If decryption fails.
        PdfParseError: If text extraction fails.
    """
    parser = PdfParser(pdf_data)
    was_encrypted = parser.is_encrypted()

    if was_encrypted:
        if not password:
            raise PdfDecryptionError("PDF is encrypted but no password provided")
        parser.decrypt(password)

    content = parser.extract_text()
    return content, was_encrypted
