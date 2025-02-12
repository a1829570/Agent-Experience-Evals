"""Using API Calls The third interaction (API Call) means that instead of manually scraping HTML (with requests + BeautifulSoup) or loading a page with a full browser (Selenium), 
your assistant makes direct requests to an external API. In other words, you’re leveraging an official or documented interface provided by the website or service."""
"""Below is an example Python script for Task 3, where your AI agent interacts with a public API (the Star Wars API at https://swapi.py4e.com/) instead of scraping a webpage. 
It follows the same OpenAI assistant and Code Interpreter workflow, but replaces HTML scraping with an API call and JSON parsing."""

"""
Task 3: API Call with the SWAPI (Star Wars API) + AI Agent
---------------------------------------------------------
This script demonstrates how to:
 1) Make an HTTP GET request to the Star Wars API (https://swapi.py4e.com/).
 2) Parse the JSON response.
 3) Feed the result to an OpenAI Assistant (with Code Interpreter enabled).
 4) Instruct the assistant to summarize the fetched data.

Note:
 - You need to install `requests` (pip install requests).
 - The Code Interpreter beta features and the 'gpt-4-turbo' model
   require appropriate OpenAI account access.
 - Replace 'YOUR_OPENAI_API_KEY_HERE' with your actual API key.
"""

import requests
from openai import OpenAI

# 1. Initialize the OpenAI Client
client = OpenAI(api_key="#inserthere")
# 2. Make an API Call to the SWAPI
#    Example: Fetch data about Luke Skywalker (character ID 1).
url = "https://swapi.py4e.com/api/people/5/" 
response = requests.get(url)

if response.status_code == 200: # A 200 status code is an HTTP response code meaning “OK”. It indicates that the server has successfully processed your request and is returning the requested data. In other words, everything worked as expected.
    data = response.json()
    
    # Convert the JSON into a string for the assistant to summarize.
    # You might want to format it more nicely or truncate if it's very large.
    swapi_content = f"{data}"

else:
    # Handle errors (e.g., 404 or 500)
    swapi_content = f"API call failed with status code {response.status_code}"

# 3. Create the Assistant (with Code Interpreter) 
assistant = client.beta.assistants.create(
    name="API Data Summarizer",
    instructions="You are an assistant that summarizes JSON or text data using Python code.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4-turbo"
)

# 4. Create a Thread for the conversation
thread = client.beta.threads.create()

# 5. Add User Message with the SWAPI Data
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=f"Summarize the following JSON data:\n\n{swapi_content}"
)

# 6. Execute the Assistant Task
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Summarize the provided JSON data in a concise way."
)

# 7. Fetch and Print the Assistant's Response
if run.status == 'completed':
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in messages.data:
        if message.role == "assistant":
            print("\nAssistant's Summary:")
            print(message.content[0].text.value)
else:
    print(f"Run status: {run.status}")




