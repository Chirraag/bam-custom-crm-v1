import os

EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SENDER_NAME = os.getenv("SENDER_NAME", "Ankit Meena")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))