# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

response = client.responses.create(
    model="gpt-4o-mini",
    input="Just say a short word"
)

print(response.output_text)
