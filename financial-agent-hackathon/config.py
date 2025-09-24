import os
from dotenv import load_dotenv

# This command looks for a .env file in the project root and loads its variables.
load_dotenv()

# Retrieve the API key from the environment variables.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# A crucial check to ensure the application doesn't run without the API key.
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please create a .env file and set the OPENAI_API_KEY.")