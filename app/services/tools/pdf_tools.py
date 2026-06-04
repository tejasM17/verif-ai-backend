import pdfplumber
from pypdf import PdfReader
from io import BytesIO
from langchain.tools import tool
from app.core.database import get_gridfs
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

@tool
async def extract_pdf_text(gridfs_doc_id: str) -> str:
    """
    Extracts all text from a PDF document stored in GridFS.
    Args:
        gridfs_doc_id: The ObjectId string of the file in GridFS.
    """
    try:
        bucket = get_gridfs("resumes")
        grid_out = await bucket.open_download_stream(ObjectId(gridfs_doc_id))
        pdf_bytes = await grid_out.read()
        
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text.strip() if text else "No text found in PDF."
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return f"Error extracting PDF text: {str(e)}"

@tool
async def extract_pdf_metadata(gridfs_doc_id: str) -> dict:
    """
    Extracts metadata (author, producer, dates, page count) from a PDF in GridFS.
    Args:
        gridfs_doc_id: The ObjectId string of the file in GridFS.
    """
    try:
        bucket = get_gridfs("resumes")
        grid_out = await bucket.open_download_stream(ObjectId(gridfs_doc_id))
        pdf_bytes = await grid_out.read()
        
        reader = PdfReader(BytesIO(pdf_bytes))
        meta = reader.metadata
        
        return {
            "creation_date": meta.get("/CreationDate", "Unknown"),
            "modification_date": meta.get("/ModDate", "Unknown"),
            "author": meta.get("/Author", "Unknown"),
            "producer": meta.get("/Producer", "Unknown"),
            "page_count": len(reader.pages)
        }
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {str(e)}")
        return {"error": str(e)}
