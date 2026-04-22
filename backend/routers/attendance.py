from fastapi import APIRouter, HTTPException
from schemas import AttendanceRequest
from services import attendance

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/upload")
async def upload_attendance(request: AttendanceRequest):
    """
    Recibe una lista de asistencia en texto y la procesa usando el servicio de asistencia.
    """
    result = attendance.process_attendance_list(request.text, request.model)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
        
    return result