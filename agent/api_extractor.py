import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from form_handling.formdetection import fill_all_forms

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Set human-like User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"


import httpx
import json
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class APIExtractor:
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=10.0)

    async def extract(self, url):
        print(f"[INFO] Checking {url} for API access...")

        try:
            response = await self.session.get(url)
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type or "application/vnd.api+json" in content_type:
                print(f"[INFO] Direct API success: {url}")
                return self._safe_json(response)

            # Not JSON: check for embedded APIs or XHR endpoints
            print(f"[ERROR] Direct API error: {response.status_code}, message='{response.reason_phrase}', url='{url}'")
            print("[INFO] Attempting to extract API endpoints from page...")
            return await self._extract_from_html(url, response.text)

        except Exception as e:
            print(f"[ERROR] APIExtractor failed for {url}: {str(e)}")
            return None

    def _safe_json(self, response):
        try:
            return response.json()
        except Exception:
            print("[ERROR] Failed to parse JSON from response.")
            return None

    async def _extract_from_html(self, base_url, html):
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script")

        api_candidates = []

        for script in scripts:
            if not script.string:
                continue
            if "fetch(" in script.string or "axios." in script.string:
                api_candidates.append(script.string)

        if api_candidates:
            print(f"[INFO] Found {len(api_candidates)} API-related scripts.")
            return {
                "type": "script-analysis",
                "candidates": api_candidates[:5]  # Limit output
            }

        return None
