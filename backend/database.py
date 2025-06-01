import os
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = "https://duxtqqxdctaoleelhrob.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR1eHRxcXhkY3Rhb2xlZWxocm9iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg3NzI2NTcsImV4cCI6MjA2NDM0ODY1N30.ufDSFHXorU71TZf_RLOiXWVBwgdgt_AAUoAWm_9IKbE"

supabase: Client = create_client(supabase_url, supabase_key)

def get_db():
    return supabase