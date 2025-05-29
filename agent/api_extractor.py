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


class APIExtractor:
    def __init__(self):
        self.api_key = api_key
        self.user_agent = USER_AGENT
        self.default_paths = ["/api", "/v1", "/graphql", "/wp-json", "/data", "/w/api.php"]
        self.extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o",
            api_token=self.api_key,
            schema={"api_url": "string", "description": "string"},
            instruction="Extract API endpoints or references from web content or JSON data."
        )

    async def check_direct_api(self, url):
        """Checks for direct API access before attempting scraping."""
        try:
            headers = {"User-Agent": self.user_agent}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        print(f"[INFO] Direct API success: {url}")
                        return await resp.json()
                    else:
                        print(f"[ERROR] API call failed with status code {resp.status}")
        except Exception as e:
            print(f"[ERROR] Direct API error: {e}")
        return None

    async def async_api_check(self, url, paths=None):
        """Checks common paths for API availability and uses LLM to extract content."""
        headers = {"User-Agent": self.user_agent}
        paths = paths or self.default_paths

        async with aiohttp.ClientSession() as session:
            tasks = [
                session.get(f"{url.rstrip('/')}{path}", headers=headers)
                for path in paths
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in responses:
                if isinstance(response, Exception):
                    print(f"Request failed: {response}")
                    continue
                if response.status == 200:
                    print(f"Potential API response at {response.url}")
                    extracted_content = self.extraction_strategy.extract_from_text(await response.text())
                    if extracted_content:
                        print("Extracted API content with LLM:", extracted_content)
                        return extracted_content
        return None

    async def extract(self, url):
        """Unified method to try direct API access and fallback to async discovery."""
        result = await self.check_direct_api(url)
        if result:
            return {"type": "api", "data": result}

        fallback = await self.async_api_check(url)
        if fallback:
            return {"type": "api", "data": fallback}

        return {"type": "none", "data": None}
