
# AX: Intelligent Agent Experience System

AX is an advanced, modular AI-driven agent designed to intelligently interact with modern websites, dynamically selecting the best method to extract relevant content based on past experience, website structure, and real-time feedback. It builds upon the foundation of the FINALAGENT system and enhances it with a reinforcement-style memory, adaptive method selection, and LLM-guided content summarization.

---

## 🌐 What It Does

AX is capable of:
- Extracting structured or unstructured content from any webpage using multiple strategies: API detection, DOM scraping, and browser automation.
- Making intelligent decisions based on past interactions (experience_log.json) and category/domain similarity (ax_memory.json).
- Dynamically switching strategies mid-run based on performance and success.
- Summarizing extracted content using LLMs for enhanced understanding and downstream use.

---

## 🧠 What Makes AX Intelligent

Unlike the original FINALAGENT.py implementation which followed a rigid strategy (API → DOM → Browser), AX introduces:

1. **Memory-Driven Strategy Selection:**
   - AX uses experience logs to record success/failure and friction scores for each method on each URL.
   - It computes the best strategy for new URLs based on exact match, domain-level similarity, or LLM-based categorization.

2. **Category-Based Intelligence:**
   - New domains inherit strategies from previously seen similar domains (e.g., seek.com.au uses the strategy that worked on indeed.com).

3. **LLM-Augmented Content Processing:**
   - After retrieving content, AX passes it to an OpenAI LLM (Assistant API) to generate concise summaries for downstream tasks.
   - Summaries are cached and used to update memory and guide future decisions.

4. **Fallback Handling:**
   - Each strategy falls back intelligently if it fails, with full trace logs and summaries of outcomes.

---

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

