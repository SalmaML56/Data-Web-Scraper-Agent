

# 📌 **AI Web Automation Agent**

An **AI-powered autonomous web automation agent** that uses **Google Gemini** to plan actions and **Playwright** to execute them.
The agent can **navigate websites, click buttons, type text, scrape data**, and achieve goals intelligently — just by describing the task in natural language.

---

## 🚀 Features

* 🤖 **AI Planner (Gemini 2.5 Flash)**
  Understands page HTML and decides the next best action (click/type/scrape/finish).

* 🌐 **Playwright Browser Automation**
  Controls Chromium with human-like behavior using stealth mode.

* 🧠 **DOM Simplification**
  Converts heavy page HTML into a clean structure for efficient LLM processing.

* 📊 **Automatic Scraping System**
  Extracts text + smart hyperlink detection.

* 🔁 **Multi-step autonomous workflow**
  AI plans → Agent executes → AI plans → Agent executes.

* 🧱 **Error handling** for slow or dynamic websites.

* 💾 **Data saved in JSON** after execution.

---

## 📂 Project Structure

```
project/
│
├── webautomationagent.py   # Main AI automation script
├── requirements.txt        # Required Python libraries
└── gemini_agent_results.json  # Output (generated automatically)
```

---

## 🔧 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo
```

### 2️⃣ Install dependencies

```
pip install -r requirements.txt
playwright install
```

---

## 🔑 Setup Google Gemini API Key

Open the script and insert your API key here:

```python
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
```

Get your key from:
👉 [https://aistudio.google.com](https://aistudio.google.com)

---

## ▶️ How to Run

```
python webautomationagent.py
```

Run karte hi program aap se puchay ga:

### 1) **Enter the URL to start at:**

Example:

```
https://www.wikipedia.org
```

### 2) **What should I do?**

Example:

```
Search Artificial Intelligence and scrape first 5 results
```

Agent khud sochy ga, plan banay ga, aur browser ko automate karega.

---

## 🧪 Example Use Cases

* Search products on Amazon & scrape prices
* Navigate Wikipedia & extract paragraph summaries
* Auto-login to dashboards (if credentials provided)
* Crawl pages, click buttons, collect data
* Automated form filling
* E-commerce data collection

---

## 📄 Output

Scraped data automatically save hoti hai:

```
gemini_agent_results.json
```

Example:

```json
[
  {
    "step": 2,
    "data": [
      {
        "text": "iPhone 15 Pro Max – $1199",
        "link": "https://example.com/item1"
      }
    ]
  }
]
```

---

## 🛡️ Disclaimer

This project is for **educational and research purposes** only.
Please follow website **robots.txt**, **terms of service**, and **legal guidelines** before automating any site.



