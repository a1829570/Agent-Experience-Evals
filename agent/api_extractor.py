import aiohttp
import asyncio
import json
import os
from dotenv import load_dotenv

async def check_direct_api(url):
    """Checks for direct API access before attempting scraping."""
    try:
        headers = {"User-Agent": USER_AGENT}
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

# Asynchronous API Path Enumeration with Crawl4AI Integration
async def async_api_check(url, paths):
    headers = {"User-Agent": "Mozilla/5.0"}
    extraction_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token=api_key,
        schema={"api_url": "string", "description": "string"},
        instruction="Extract API endpoints or references from web content or JSON data."
    )

    async with aiohttp.ClientSession() as session:
        tasks = [
            session.get(f"{url.rstrip('/')}{path}", headers=headers) for path in paths
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                print(f"Request failed: {response}")
                continue
            if response.status == 200:
                print(f"Potential API response at {response.url}")
                extracted_content = extraction_strategy.extract_from_text(await response.text())
                if extracted_content:
                    print("Extracted API content with LLM:", extracted_content)
                    return extracted_content
    return None