from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from database import get_db, supabase
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

router = APIRouter()


class NoteBase(BaseModel):
    # Allow extra fields to be included in the model
    model_config = ConfigDict(extra="allow")

    client_id : str
    created_by : str
    content : str
    updated_at : Optional[str] = None


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    content: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/{client_id}", response_model=List[dict])
async def get_notes(client_id: str):
    try:
        logger.info("Fetching all notes")
        response = supabase.table("notes").select("*").eq("client_id", client_id).execute()
        logger.info(f"Successfully retrieved {len(response.data)} notes")
        return response.data
    except Exception as e:
        logger.error(f"Failed to fetch notes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch notes: {str(e)}")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_note(note:NoteBase):
    try:
        
        # Validate required fields
        if not note.client_id or not note.created_by or not note.content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Client ID, Created By, and Content are required")

        logger.info(f"Creating new note for client: {note.client_id}")

        if not note.created_by:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Created by is required")

        # Convert note to dict (this now includes extra fields thanks to extra="allow")
        note_data = note.model_dump()
        logger.info(f"Note data before processing: {note_data}")
        # Add timestamps
        note_data["created_at"] = datetime.now().isoformat()
        note_data["updated_at"] = note_data["created_at"]

        # Remove None values to avoid overwriting database defaults
        note_data = {k: v for k, v in note_data.items() if v is not None}

        response = supabase.table("notes").insert(note_data).execute()
        new_note = response.data[0]
        logger.info(f"Successfully created note with ID: {new_note['id']}")
        return new_note
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to create note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to create note: {str(e)}")


@router.put("")
async def update_note(note: NoteBase):
    try:
        note_id = note.model_dump().get("id")
        logger.info(f"Received request to update note with ID: {note_id}")
        if not note_id:
            logger.error("Note ID is required for update")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Note ID is required for update")
        logger.info(f"Updating note with ID: {note_id}")

        # First check if note exists
        check_response = supabase.table("notes").select("*").eq(
            "id", note_id).execute()
        if not check_response.data:
            logger.warning(
                f"Note with ID {note_id} not found during update")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with ID {note_id} not found")

        # Get note data including extra fields
        note_data = note.model_dump(exclude_unset=True)

        # Add updated timestamp
        note_data["updated_at"] = datetime.now().isoformat()

        # Remove None values to avoid overwriting existing data with None
        note_data = {k: v for k, v in note_data.items() if v is not None}

        logger.info(f"Update data: {note_data}")

        response = supabase.table("notes").update(note_data).eq(
            "id", note_id).execute()
        logger.info(f"Successfully updated note with ID: {note_id}")
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to update note {note_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to update note: {str(e)}")


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str):
    try:
        logger.info(f"Attempting to delete note with ID: {note_id}")

        # First check if note exists
        check_response = supabase.table("notes").select("*").eq(
            "id", note_id).execute()
        if not check_response.data:
            logger.warning(
                f"Note with ID {note_id} not found during deletion")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Note with ID {note_id} not found")

        response = supabase.table("notes").delete().eq("id", note_id).execute()
        logger.info(f"Successfully deleted note with ID: {note_id}")
        return None
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to delete note {note_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to delete note: {str(e)}")


# # Optional: Add an endpoint to get all possible fields for a client
# @router.get("/schema/fields")
# async def get_client_fields():
#     """Get all possible fields for client records by querying the database schema"""
#     try:
#         # This is a sample query - adjust based on your database system
#         # For PostgreSQL/Supabase, you might query information_schema
#         logger.info("Fetching client schema fields")

#         # Get a sample client to see all available fields
#         response = supabase.table("clients").select("*").limit(1).execute()
#         if response.data:
#             available_fields = list(response.data[0].keys())
#             return {"available_fields": available_fields}
#         else:
#             # Return the known fields from the model
#             known_fields = list(ClientBase.model_fields.keys())
#             return {"available_fields": known_fields}

#     except Exception as e:
#         logger.error(f"Failed to fetch client fields: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail=f"Failed to fetch client fields: {str(e)}")
