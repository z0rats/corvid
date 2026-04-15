import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import (
    extract_iocs,
    extract_iocs_from_file_content
)
from app.features.ioc_tools.ioc_extractor.utils.validation_utils import (
    validate_file_upload,
    decode_file_content,
    get_file_extension
)
from app.features.ioc_tools.ioc_extractor.schemas.extractor_schemas import (
    TextExtractionRequest,
    ExtractionResponse,
    ExtractionErrorResponse,
    FileUploadInfo
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/api/extractor/",
    tags=["IOC Extractor"],
    response_model=ExtractionResponse,
    responses={
        400: {"model": ExtractionErrorResponse, "description": "Invalid file or processing error"},
        413: {"model": ExtractionErrorResponse, "description": "File too large"},
        422: {"model": ExtractionErrorResponse, "description": "Validation error"},
        500: {"model": ExtractionErrorResponse, "description": "Internal server error"}
    }
)
async def extract_iocs_from_file(file: UploadFile = File(...)) -> ExtractionResponse:
    """
    Extract IOCs from uploaded file content
    
    This endpoint accepts file uploads and extracts IOCs from the file content.
    Supports various text-based file formats and handles multiple character encodings.
    
    Args:
        file: Uploaded file containing text with potential IOCs
        
    Returns:
        ExtractionResponse with extracted IOCs and statistics
        
    Raises:
        HTTPException: For file validation errors or processing failures
    """
    logger.info("Received file upload for IOC extraction: %s", file.filename)
    
    is_valid, error_message = validate_file_upload(file)
    if not is_valid:
        logger.warning("File validation failed: %s", error_message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation error: {error_message}"
        )
    
    try:
        file_contents = await file.read()
        
        # Decode file content
        try:
            file_contents_str, encoding_used = decode_file_content(file_contents)
            logger.info("Successfully decoded file using encoding: %s", encoding_used)
        except UnicodeDecodeError as e:
            logger.error("Failed to decode file %s: %s", file.filename, str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to decode file content. Supported encodings: utf-8, latin-1, ascii, iso-8859-1, cp1252"
            )
        
        result = extract_iocs_from_file_content(file_contents_str, file.filename)
        
        logger.info("Successfully extracted IOCs from file: %s", file.filename)
        return result
        
    except ValueError as e:
        logger.warning("Validation error processing file %s: %s", file.filename, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File processing error: {str(e)}"
        )
        
    except RuntimeError as e:
        logger.error("Runtime error processing file %s: %s", file.filename, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
        
    except Exception as e:
        logger.error("Unexpected error processing file %s: %s", file.filename, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file processing"
        )


@router.post(
    "/api/extractor/text/",
    tags=["IOC Extractor"],
    response_model=ExtractionResponse,
    responses={
        400: {"model": ExtractionErrorResponse, "description": "Invalid text or processing error"},
        422: {"model": ExtractionErrorResponse, "description": "Validation error"},
        500: {"model": ExtractionErrorResponse, "description": "Internal server error"}
    }
)
async def extract_iocs_from_text(request: TextExtractionRequest) -> ExtractionResponse:
    """
    Extract IOCs from plain text input
    
    This endpoint accepts plain text and extracts IOCs from it. It's used by other
    components like the defang tool and provides comprehensive IOC recognition.
    
    Args:
        request: TextExtractionRequest containing text to process
        
    Returns:
        ExtractionResponse with extracted IOCs and statistics
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    logger.info("Received text-based IOC extraction request")
    
    try:
        result = extract_iocs(request.text)
        
        logger.info("Successfully extracted IOCs from text input")
        return result
        
    except ValueError as e:
        logger.warning("Validation error in text extraction: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text validation error: {str(e)}"
        )
        
    except RuntimeError as e:
        logger.error("Runtime error in text extraction: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
        
    except Exception as e:
        logger.error("Unexpected error in text extraction: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during text processing"
        )
