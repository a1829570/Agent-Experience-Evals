def categorize_content(html: str) -> str:
    import re, time
    from openai import OpenAI
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    cleaned = re.sub(r'\s+', ' ', html)[:3000]

    try:
        assistant = client.beta.assistants.create(
            name="Domain Category Classifier",
            instructions="""You are a classifier that returns one category for HTML content: 
            jobs, news, ecommerce, academic, media, api, wiki, or other. 
            Respond with just one of those labels, nothing else.""",
            tools=[],
            model="gpt-4o"
        )

        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=html[:3000]
        )

        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value.strip().lower()

        if "job" in response:
            return "jobs"
        elif "news" in response:
            return "news"
        elif "ecommerce" in response or "shopping" in response or "retail" in response:
            return "ecommerce"
        elif "academic" in response or "education" in response:
            return "academic"
        elif "media" in response or "entertainment" in response:
            return "media"
        elif "api" in response or "json" in response or "structured" in response:
            return "api"
        elif "wiki" in response or "encyclopedia" in response:
            return "wiki"
        else:
            return "other"

    except Exception as e:
        print(f"[ERROR] Categorization failed: {e}")
        return "other"
