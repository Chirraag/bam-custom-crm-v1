from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Union, Dict
from datetime import datetime
from database import get_db, supabase
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

router = APIRouter()


class ClientBase(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    name_prefix: Optional[str] = None
    name_suffix: Optional[str] = None
    full_name: Optional[str] = None
    primary_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    fax_phone: Optional[str] = None
    primary_email: Optional[str] = None
    alternate_email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "United States"
    home_address_line1: Optional[str] = None
    home_address_line2: Optional[str] = None
    home_city: Optional[str] = None
    home_state: Optional[str] = None
    home_zip_code: Optional[str] = None
    home_country: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None
    case_type: Optional[str] = None
    case_status: Optional[str] = None
    case_date: Optional[str] = None
    date_of_injury: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    preferred_language: Optional[str] = "English"
    communication_preference: Optional[str] = None
    record_manager: Optional[str] = None
    created_by: Optional[str] = None
    user_defined_fields: Optional[Dict[str, str]] = {}
    client_documents: Optional[Dict[str, str]] = {}


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


@router.get("", response_model=List[dict])
async def get_clients():
    try:
        logger.info("Fetching all clients")
        response = supabase.table("clients").select("*").execute()
        logger.info(f"Successfully retrieved {len(response.data)} clients")
        return response.data
    except Exception as e:
        logger.error(f"Failed to fetch clients: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch clients: {str(e)}")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_client(client: ClientCreate):
    try:
        logger.info(
            f"Creating new client: {client.first_name} {client.last_name}")

        # Validate required fields
        if not client.first_name or not client.last_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="First name and last name are required")

        if not client.created_by:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Created by is required")

        # Convert client to dict and add timestamps
        client_data = client.dict()
        client_data["created_at"] = datetime.utcnow().isoformat()
        client_data["updated_at"] = client_data["created_at"]

        # Ensure dates are in ISO format string
        date_fields = ["birth_date", "case_date", "date_of_injury"]
        for field in date_fields:
            if client_data.get(field):
                try:
                    parsed_date = datetime.strptime(client_data[field],
                                                    "%Y-%m-%d")
                    client_data[field] = parsed_date.date().isoformat()
                except ValueError:
                    logger.error(
                        f"Invalid date format for {field}: {client_data[field]}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=
                        f"Invalid date format for {field}. Expected format: YYYY-MM-DD"
                    )

        response = supabase.table("clients").insert(client_data).execute()
        new_client = response.data[0]
        logger.info(f"Successfully created client with ID: {new_client['id']}")
        return new_client
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to create client: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to create client: {str(e)}")


@router.get("/{client_id}", response_model=dict)
async def get_client(client_id: Union[str, int]):
    try:
        logger.info(f"Fetching client with ID: {client_id}")
        response = supabase.table("clients").select("*").eq(
            "id", client_id).execute()
        if not response.data:
            logger.warning(f"Client with ID {client_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Client with ID {client_id} not found")
        logger.info(f"Successfully retrieved client with ID: {client_id}")
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to fetch client {client_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch client: {str(e)}")


@router.put("/{client_id}")
async def update_client(client_id: Union[str, int], client: ClientUpdate):
    try:
        logger.info(f"Updating client with ID: {client_id}")
        logger.info(f"Client data: {client.dict()}")
        # First check if client exists
        check_response = supabase.table("clients").select("*").eq(
            "id", client_id).execute()
        if not check_response.data:
            logger.warning(
                f"Client with ID {client_id} not found during update")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Client with ID {client_id} not found")

        # Update the client
        client_data = client.dict(exclude_unset=True)
        client_data["updated_at"] = datetime.utcnow().isoformat()

        # Handle date fields
        date_fields = ["birth_date", "case_date", "date_of_injury"]
        for field in date_fields:
            if client_data.get(field):
                try:
                    parsed_date = datetime.strptime(client_data[field],
                                                    "%Y-%m-%d")
                    client_data[field] = parsed_date.date().isoformat()
                except ValueError:
                    logger.error(
                        f"Invalid date format for {field}: {client_data[field]}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=
                        f"Invalid date format for {field}. Expected format: YYYY-MM-DD"
                    )

        response = supabase.table("clients").update(client_data).eq(
            "id", client_id).execute()
        logger.info(f"Successfully updated client with ID: {client_id}")
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to update client {client_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to update client: {str(e)}")


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: Union[str, int]):
    try:
        logger.info(f"Attempting to delete client with ID: {client_id}")
        # First check if client exists
        check_response = supabase.table("clients").select("*").eq(
            "id", client_id).execute()
        if not check_response.data:
            logger.warning(
                f"Client with ID {client_id} not found during deletion")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Client with ID {client_id} not found")

        # Delete associated documents from storage
        if check_response.data[0].get('client_documents'):
            try:
                folder_name = f"client_{client_id}"
                supabase.storage.from_('client-documents').remove(
                    [folder_name])
            except Exception as e:
                logger.warning(f"Failed to delete client documents: {str(e)}")

        response = supabase.table("clients").delete().eq("id",
                                                         client_id).execute()
        logger.info(f"Successfully deleted client with ID: {client_id}")
        return None
    except Exception as e:
        logger.error(f"Failed to delete client {client_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to delete client: {str(e)}")
