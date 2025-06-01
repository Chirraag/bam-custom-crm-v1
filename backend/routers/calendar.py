from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from database import get_db, supabase

router = APIRouter()

class AppointmentBase(BaseModel):
    title: str
    client_id: int
    date: date
    time: str
    appointment_type: str
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    client_id: Optional[int] = None
    date: Optional[date] = None
    time: Optional[str] = None
    appointment_type: Optional[str] = None
    notes: Optional[str] = None

class Appointment(AppointmentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

@router.get("/", response_model=List[Appointment])
async def get_appointments():
    try:
        response = supabase.table("appointments").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch appointments: {str(e)}"
        )

@router.get("/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: int):
    try:
        response = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found"
            )
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch appointment: {str(e)}"
        )

@router.post("/", response_model=Appointment, status_code=status.HTTP_201_CREATED)
async def create_appointment(appointment: AppointmentCreate):
    try:
        # Check if client exists
        client_check = supabase.table("clients").select("id").eq("id", appointment.client_id).execute()
        if not client_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {appointment.client_id} not found"
            )
        
        response = supabase.table("appointments").insert(appointment.dict()).execute()
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}"
        )

@router.put("/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: int, appointment: AppointmentUpdate):
    try:
        # First check if appointment exists
        check_response = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
        if not check_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found"
            )
        
        # Filter out None values
        update_data = {k: v for k, v in appointment.dict().items() if v is not None}
        
        # If client_id is being updated, check if the client exists
        if "client_id" in update_data:
            client_check = supabase.table("clients").select("id").eq("id", update_data["client_id"]).execute()
            if not client_check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Client with ID {update_data['client_id']} not found"
                )
        
        # Update appointment
        response = supabase.table("appointments").update(update_data).eq("id", appointment_id).execute()
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appointment: {str(e)}"
        )

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(appointment_id: int):
    try:
        # First check if appointment exists
        check_response = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
        if not check_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found"
            )
        
        # Delete appointment
        supabase.table("appointments").delete().eq("id", appointment_id).execute()
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete appointment: {str(e)}"
        )