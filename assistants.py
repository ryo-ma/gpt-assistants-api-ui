import os
import base64
import re
import json

from openai import AzureOpenAI
from openai import AssistantEventHandler
from tools import TOOL_MAP
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())

azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
api_version = os.environ.get("AZURE_API_VERSION")


client = AzureOpenAI(
    api_key=azure_openai_key,
    api_version=api_version,
    azure_endpoint=azure_openai_endpoint
)

assistants = client.beta.assistants.list(
    order="desc",
    limit="20"
)

output = assistants.data

#get all existing assistantsassistants_json = json.loads(get_extracted_data())
assistants_list = [{"id": assistant.id, "title": assistant.name} for assistant in output] 

def current_assistants():  
    return json.dumps(assistants_list)