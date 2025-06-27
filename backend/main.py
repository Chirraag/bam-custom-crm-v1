from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from helper.email_reciever import check_inbox 
import time
import threading

# Load environment variables
load_dotenv()

# Configure root logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Create logger for this module
logger = logging.getLogger(__name__)

# Import routers
from routers import clients, calendar, messages, notes, mail

app = FastAPI(title="Law Firm CRM API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow credentials
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Include routers
app.include_router(clients.router, prefix="/api/clients", tags=["clients"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(mail.router, prefix="/api/mail", tags=["mail"])


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Law Firm CRM API"}


@app.get("/api/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


def start_polling():
    while True:
        check_inbox() 
        time.sleep(60)  # Poll every 60 seconds

@app.on_event("startup")
def startup_event():
    print("🚀 Starting email poller thread")
    load_dotenv()
    threading.Thread(target=start_polling, daemon=True).start()