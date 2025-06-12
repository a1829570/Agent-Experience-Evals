# agent/llm_categorizer.py

import re
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def categorize_content(html: str) -> str:
    cleaned = re.sub(r'\s+', ' ', html)[:3000]

    assistant = client.beta.assistants.create(
        name="Page Categorizer",
        instructions="You're a classifier that returns one category for HTML: jobs, news, ecommerce, academic, media, or general.",
        model="gpt-4o"
    )

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Classify this HTML page into one of the following categories: jobs, news, ecommerce, academic, media, general.\n\n{cleaned}"
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while True:
        current_run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if current_run.status == "completed":
            break
        elif current_run.status in ["failed", "cancelled", "expired"]:
            return "general"
        time.sleep(2)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in messages.data:
        if message.role == "assistant":
            return message.content[0].text.value.strip().lower()

    return "general"
