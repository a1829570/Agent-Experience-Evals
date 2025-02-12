"""The Selenium version of the assistant uses a browser automation approach, enabling it to handle dynamic websites that rely on JavaScript or user interactions. 
By simulating real-user actions such as logging in, clicking “Load More” buttons, and waiting for elements to appear, it can scrape data that might not be visible 
when simply fetching static HTML. This makes it ideal for complex sites where content is loaded after page load or requires form submissions to access.
This example uses Selenium to open the webpage, retrieve the page source, and then extracts the text using BeautifulSoup. 
The rest of the steps (using the OpenAI client, creating an assistant, creating a thread, etc.) remain the same structure as your original code."""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from openai import OpenAI

"""Selenium WebDriver is a tool in the Selenium suite that automates browser actions by directly
 communicating with each browser through a dedicated driver (e.g., ChromeDriver or GeckoDriver).
 It lets you write code in languages like Python or Java to open webpages, click elements, fill out forms,
   and take screenshots—essentially executing any browser-based task programmatically. 
   This facilitates web application testing, web scraping, or other automation tasks without 
   requiring manual browser interaction."""

client = OpenAI(api_key="#inserthere")
# Fetch webpage content with Selenium
url = "https://en.wikipedia.org/wiki/Cristiano_Ronaldo"

# Set up Chrome options (for headless use, if desired)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Running Chrome (or any browser) in headless mode means it won’t display a graphical user interface (no actual browser window pops up). There are several benefits to doing this for web-scraping or automation tasks:

# Create a new WebDriver instance. Automatically download and manage the appropriate ChromeDriver version
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.get(url)

# Grab the page source
page_source = driver.page_source
driver.quit()

# Now, parse the page source with BeautifulSoup
soup = BeautifulSoup(page_source, 'html.parser')
webpage_content = soup.get_text() #Extract the text content from the webpage

# Create Assistant with Code Interpreter
assistant = client.beta.assistants.create(
    name="Web Content Summarizer",
    instructions="You are an assistant that summarizes text data using Python code.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4-turbo"
)

# Create a Thread
thread = client.beta.threads.create()

# Add User Message with Web Content
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=f"Summarize the following text:\n\n{webpage_content[:3000]}"  # Truncate to fit model limits
)

# Execute the Assistant Task
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Summarize the provided text."
)

# Fetch and Print the Assistant's Response
if run.status == 'completed':
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in messages.data:
        if message.role == "assistant":
            print(message.content[0].text.value)
else:
    print(f"Run status: {run.status}")
