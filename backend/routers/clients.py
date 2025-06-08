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


class ClientBase(BaseModel):
    # Allow extra fields to be included in the model
    model_config = ConfigDict(extra="allow")

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
    # For updates, make all fields optional including first_name and last_name
    first_name: Optional[str] = None
    last_name: Optional[str] = None


def process_date_fields(client_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process date fields to ensure they are in ISO format"""
    date_fields = ["birth_date", "case_date", "date_of_injury"]

    for field in date_fields:
        if client_data.get(field):
            try:
                # Handle different date formats
                date_value = client_data[field]
                if isinstance(date_value, str):
                    # Try different date formats
                    date_formats = [
                        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
                        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"
                    ]
                    parsed_date = None

                    for date_format in date_formats:
                        try:
                            parsed_date = datetime.strptime(
                                date_value.split('T')[0]
                                if 'T' in date_value else date_value,
                                date_format.split('T')[0]
                                if 'T' in date_format else date_format)
                            break
                        except ValueError:
                            continue

                    if parsed_date:
                        client_data[field] = parsed_date.date().isoformat()
                    else:
                        logger.error(
                            f"Invalid date format for {field}: {client_data[field]}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=
                            f"Invalid date format for {field}. Expected formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY"
                        )
            except ValueError as ve:
                logger.error(
                    f"Invalid date format for {field}: {client_data[field]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=
                    f"Invalid date format for {field}. Expected formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY"
                )

    return client_data


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

        # Convert client to dict (this now includes extra fields thanks to extra="allow")
        client_data = client.model_dump()

        # Add timestamps
        client_data["created_at"] = datetime.utcnow().isoformat()
        client_data["updated_at"] = client_data["created_at"]

        # Process date fields
        client_data = process_date_fields(client_data)

        # Remove None values to avoid overwriting database defaults
        client_data = {k: v for k, v in client_data.items() if v is not None}

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
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to fetch client {client_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch client: {str(e)}")


@router.put("/{client_id}")
async def update_client(client_id: Union[str, int], client: ClientUpdate):
    try:
        logger.info(f"Updating client with ID: {client_id}")

        # First check if client exists
        check_response = supabase.table("clients").select("*").eq(
            "id", client_id).execute()
        if not check_response.data:
            logger.warning(
                f"Client with ID {client_id} not found during update")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Client with ID {client_id} not found")

        # Get client data including extra fields
        client_data = client.model_dump(exclude_unset=True)

        # Add updated timestamp
        client_data["updated_at"] = datetime.utcnow().isoformat()

        # Process date fields
        client_data = process_date_fields(client_data)

        # Remove None values to avoid overwriting existing data with None
        client_data = {k: v for k, v in client_data.items() if v is not None}

        logger.info(f"Update data: {client_data}")

        response = supabase.table("clients").update(client_data).eq(
            "id", client_id).execute()
        logger.info(f"Successfully updated client with ID: {client_id}")
        return response.data[0]
    except HTTPException as he:
        raise he
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
                logger.info(
                    f"Deleted client documents for client ID: {client_id}")
            except Exception as e:
                logger.warning(f"Failed to delete client documents: {str(e)}")

        response = supabase.table("clients").delete().eq("id",
                                                         client_id).execute()
        logger.info(f"Successfully deleted client with ID: {client_id}")
        return None
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to delete client {client_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to delete client: {str(e)}")


# Optional: Add an endpoint to get all possible fields for a client
@router.get("/schema/fields")
async def get_client_fields():
    """Get all possible fields for client records by querying the database schema"""
    try:
        # This is a sample query - adjust based on your database system
        # For PostgreSQL/Supabase, you might query information_schema
        logger.info("Fetching client schema fields")

        # Get a sample client to see all available fields
        response = supabase.table("clients").select("*").limit(1).execute()
        if response.data:
            available_fields = list(response.data[0].keys())
            return {"available_fields": available_fields}
        else:
            # Return the known fields from the model
            known_fields = list(ClientBase.model_fields.keys())
            return {"available_fields": known_fields}

    except Exception as e:
        logger.error(f"Failed to fetch client fields: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch client fields: {str(e)}")
