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
from formdetection import (
    fill_all_forms,  # main function that detects & fills forms
)
# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)




def process_web_content(content):
    print("Processing Web Content...")
    assistant = client.beta.assistants.create(
        name="Web Content Summarizer",
        instructions="You are an assistant that extracts and summarizes web data using Python.",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4-turbo"
    )

    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Extract and summarize the following content:\n\n{content[:3000]}"
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Extract key information from the provided content."
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == "assistant":
                print(message.content[0].text.value)
    else:
        print(f"Run status: {run.status}")