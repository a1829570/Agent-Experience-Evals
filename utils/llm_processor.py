import aiohttp
import asyncio
from seleniumwire import webdriver  # For network intercept
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
import random
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
import os
from dotenv import load_dotenv
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from selenium.common.exceptions import MoveTargetOutOfBoundsException
import undetected_chromedriver as uc
from twocaptcha import TwoCaptcha
import asyncio
import logging
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from twocaptcha import TwoCaptcha
import requests
import json
import logging
import random
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from form_handling.formdetection import (
    fill_all_forms,  # main function that detects & fills forms
)
import re
# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)




def process_web_content(content):
    print("Processing Web Content...")

    # Clean and truncate content
    cleaned = re.sub(r'\s+', ' ', content)
    content_to_send = cleaned[:3000]

    # Create assistant
    assistant = client.beta.assistants.create(
        name="Web Extractor",
        instructions="You are a helpful assistant that extracts structured key points such as names, dates, locations, and facts from HTML web content. Focus on clarity and brevity.",
        model="gpt-4o",
        tools=[{"type": "code_interpreter"}]
    )

    # Create thread and send message
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Extract and summarize key facts from this page content:\n\n{content_to_send}"
    )

    # Start run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Focus on summarizing the most important content from the user's message."
    )

    # Poll run status
    while True:
        current_run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if current_run.status == "completed":
            break
        elif current_run.status in ["failed", "cancelled", "expired"]:
            print(f"Run status: {current_run.status}")
            if current_run.last_error:
                print("Error details:", current_run.last_error)
            return
        time.sleep(2)

    # Get assistant message response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in messages.data:
        if message.role == "assistant":
            print(message.content[0].text.value)