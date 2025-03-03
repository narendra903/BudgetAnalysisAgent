# 💰 Indian Budget Analysis AI Assistant

## 📌 Overview
The **Indian Budget Analysis AI Assistant** is a Streamlit-based AI-powered tool that provides insights, analysis, and recommendations based on the **Indian Union Budget 2025-26**. It leverages:
- **Agno AI** for AI-driven responses.
- **LanceDB** as a vector database for storing and retrieving budget-related documents.
- **Gemini Models** for NLP-based understanding and response generation.
- **DuckDuckGoTools** for real-time web search and financial data retrieval.

## 🚀 Features
- **AI-Powered Analysis**: Uses Gemini AI models to provide structured insights.
- **Knowledge Base Integration**: Combines information from PDFs, websites, and web search.
- **Web Search**: Uses DuckDuckGo for retrieving real-time budget updates.
- **Document Processing**: Parses official budget documents (local & online PDFs) for structured data analysis.
- **Interactive UI**: Built with Streamlit, featuring custom styling and enhanced user experience.

## 🏗️ Tech Stack
- **Python** (Primary programming language)
- **Streamlit** (Web app framework)
- **Agno AI** (AI agent framework)
- **LanceDB** (Vector database for knowledge storage)
- **Gemini AI** (Google AI models for embeddings and responses)
- **AsyncIO & AIOHTTP** (For async URL fetching and data retrieval)
- **Plotly** (For visual data representation)

## 📂 Project Structure
```
📦 Indian-Budget-AI
├── 📜 main.py          # Main Streamlit application
├── 📜 .env             # Environment variables (API keys)
├── 📜 requirements.txt # Dependencies
├── 📜 README.md        # Documentation
└── 📂 tmp/lancedb      # Vector database storage
```

## 🛠️ Installation & Setup
### 1️⃣ Clone the Repository
```bash
git clone https://github.com/narendra903/BudgetAnalysisAgent.git
cd Indian-Budget-AI
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Set Up Environment Variables
Create a `.env` file in the root directory and add:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4️⃣ Run the Application
```bash
streamlit run main.py
```

## 📊 How It Works
1. **Loads Knowledge Bases**: Retrieves data from:
   - Local budget PDF documents
   - Online budget reports
   - Government and financial news websites
2. **AI-Powered Query Handling**:
   - Uses the `knowledge_agent` to answer from stored documents
   - If no relevant information is found, the `searcher` agent performs web search
3. **Structured Responses**:
   - Provides insights with markdown formatting, tables, and charts

## ⚡ Future Enhancements
- **Improved Visualization**: Advanced charts & graphs for data analysis.
- **Multi-Agent Collaboration**: Enhanced AI workflow for better insights.
- **Live Stock Market Integration**: Direct analysis of budget impact on stocks.

## 🤝 Contributing
We welcome contributions! Feel free to submit issues, feature requests, or PRs.

## 📜 License
This project is licensed under the **MIT License**.

Contact
Creator: Narendra (AI & Finance Enthusiast)

Email: narendra.insights@gmail.com

LinkedIn: Narendra's Profile

For questions, feedback, or collaboration, feel free to reach out!

---
🚀 Built for insightful **Indian Budget Analysis** & **Financial Research**!

