
# AX: Intelligent Agent Experience System

AX is an advanced, modular AI-driven agent designed to intelligently interact with modern websites, dynamically selecting the best method to extract relevant content based on past experience, website structure, and real-time feedback. It builds upon the foundation of the FINALAGENT system and enhances it with a reinforcement-style memory, adaptive method selection, and LLM-guided content summarization.

---

🧠 AX Workflow

The AX Agent’s workflow is a five-phase pipeline:

### 1. 🔗 URL Intake  
Reads target websites from `websites.txt` and processes them one by one.

### 2. 📚 Memory Lookup + Category Inference  
- If the domain was seen before, AX reuses the best-scoring strategy.
- If new, it infers a **semantic category** using OpenAI LLMs or prior examples.
- It chooses the best method used on similar sites (e.g., job boards, universities).

### 3. 🛠 Method Execution  
Executes one of the following strategies:
- `api`: Extracts content via network calls or API endpoints
- `dom`: Pulls page source directly, even if JS-rendered
- `browser`: Uses Selenium to simulate full human interaction

Falls back if a method fails and logs each attempt.

### 4. 🧠 LLM Summarization  
Summarizes the extracted content using a conversational LLM (via OpenAI Assistants API), yielding clean, readable output.

### 5. 📊 Logging + Feedback  
- Updates `ax_memory.json` with method performance by domain & category
- Stores experiences in `experience_log.json`
- Generates success graphs, runtime visualizations, and friction metrics

---

## 💡 What Makes It Intelligent?

| Feature                             | `FINALAGENT.py` | **AX Agent** |
|------------------------------------|------------------|--------------|
| Fixed order (api → dom → browser)  | ✅               | ❌           |
| Reuses best strategy by domain     | ❌               | ✅           |
| Learns by semantic category        | ❌               | ✅           |
| LLM summarization of content       | ❌               | ✅           |
| Tracks runtime + friction          | ❌               | ✅           |
| Visualizes performance             | ❌               | ✅           |
| Intelligent retry + method selection | ❌             | ✅           |

AX Agent is built with **modularity, memory, and reasoning** to improve with every execution.


## 📁 Repository Structure

```
├── main.py                   # Entry point for AX runs
├── FINALAGENT.py             # Original baseline agent
├── ax_memory.py              # Category/domain memory logic
├── experience_logger.py      # Experience log handler
├── api_extractor.py          # API extraction strategies
├── dom_scraper.py            # Static and dynamic scraping
├── browser_controller.py     # Selenium stealth automation
├── llm_processor.py          # LLM integration & summarization
├── formdetection.py          # Optional: Form skipping/filling
├── websites.txt              # List of URLs to process
├── experience_log.json       # Logs all visits, success, friction
├── ax_memory.json            # Memory of strategies by category/domain
```

---

## ▶️ How to Run

### 1. Clone and Setup Environment
```bash
git clone https://github.com/your-org/AX-agent.git
cd AX-agent
pip install -r requirements.txt
```

### 2. Set Your OpenAI API Key
Create a `.env` file or export manually:
```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Add URLs
Edit `websites.txt` to add your list of URLs.

### 4. Run the Agent
```bash
python3 main.py
```

You’ll see detailed logs, summaries, method performance, and fallback results.

---

## 📊 Metrics & Graphing

AX logs all outcomes and scores per strategy. After running, it automatically:
- Visualizes success rates across strategies.
- Shows which strategy performs best per category/domain.
- Logs summary content from LLMs.

---

## 📌 Future Enhancements

- Reinforcement learning loop using strategy performance as reward.
- Offline summarization model for cost saving.
- Human-in-the-loop form filling and annotation interface.

---

## 🧠 Built With Intelligence First

AX is not just a scraping agent. It is a learning, adapting, and summarizing agent, purpose-built to intelligently interact with the web and refine its approach over time.

