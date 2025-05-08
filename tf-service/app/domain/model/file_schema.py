from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    filename: str
    message: str
    original_path: str
    mosaic_path: Optional[str] = None
    faces_detected: int = 0

class MosaicResult(BaseModel):
    success: bool
    error: str = ""
    faces_detected: int = 0
    
class HandwrittenPredictionResponse(BaseModel):
    predicted_digit: int
    confidence: float
    file_path: str
