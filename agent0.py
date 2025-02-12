# Workflow
""" Assistant Creation:

Created an assistant with the code_interpreter tool, but it didn’t interact with the webpage directly.
Message Content:

You asked the assistant to "Fetch and summarize the content of [a URL]".
The assistant used its pre-trained knowledge (up to December 2023) to provide a response because the code_interpreter tool doesn’t have live web access.
Outcome:

The assistant gave a summary of Cristiano Ronaldo based on its internal knowledge, not the actual webpage content.
The task didn't utilize any external processing. 


Key Issue: current API tools prevent direct web access to pages (e.g. web_browser), need to preprocess the page into a format that this code can read
"""





from openai import OpenAI  # Import the OpenAI client
import os
from dotenv import load_dotenv
# Initialize OpenAI client\# Step 1: Set OpenAI API Key (Replace with your provided key)
# This authenticates your requests with OpenAI's servers.

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# Step 2: Create an Assistant
# Assistants are entities with specific capabilities, such as fetching web content or summarizing data.
assistant = client.beta.assistants.create(
    name="Web Fetcher",  # Name of the assistant
    instructions="You are a web-fetching assistant that obtains and summarizes content from the web.",  # Define the assistant's behavior
    tools=[{"type": "code_interpreter"}],  # Tools available to the assistant (e.g., code interpreter)
    model="gpt-4-turbo"  # Use the correct model name (fixed from "gpt-4o")
)

# Step 3: Create a Thread
# A Thread represents a conversation or session between the user and the assistant.
thread = client.beta.threads.create()

# Step 4: Add a User Message to the Thread
# Messages are the primary way to interact with the assistant in a thread.
message = client.beta.threads.messages.create(
    thread_id=thread.id,  # Specify the thread to which the message belongs
    role="user",  # Define the role of the sender (user or assistant)
    content="Fetch and summarize the content of https://en.wikipedia.org/wiki/Cristiano_Ronaldo"  # User's request
)

# Step 5: Create a Run
# A Run executes the assistant's task using the tools and instructions defined earlier.
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,  # Specify the thread to use
    assistant_id=assistant.id,  # Specify the assistant to run
    instructions="Summarize the key points of the website."  # Provide specific instructions for the task
)

# Step 6: Check Run Status and Fetch Messages
if run.status == 'completed':  # If the task is completed
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    print(messages)  # Print the full list of messages
else:
    print(f"Run status: {run.status}")  # Print the current status if not completed
