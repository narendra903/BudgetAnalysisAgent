import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
import os
import time
import requests  # For synchronous HTTP requests
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.lancedb import LanceDb
from agno.embedder.google import GeminiEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.models.google import Gemini
from textwrap import dedent
from agno.vectordb.search import SearchType
import plotly.express as px
import re

# Load environment variables
load_dotenv()
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not api_key:
    st.error("⚠️ API Key not found. Please set GEMINI_API_KEY in .env or Streamlit secrets.")
    st.stop()

embedder = GeminiEmbedder(id="models/text-embedding-004", dimensions=768, api_key=api_key)

# Custom CSS for gradient background
page_bg_css = """
<style>
    html, body, [class*="css"]  {
        min-height: 100vh;
        background: linear-gradient(to right, #f7f9fc, #ddeeff);
        color: white;
    }
    .stApp {
        background: transparent;
        min-height: 100vh;
    }
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea, 
    .stButton>button {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: #333 !important;
        border: 1px solid #aaccee !important;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background-color: #aaccee !important;
        color: #333 !important;
        border-radius: 12px;
        font-size: 16px;
        padding: 10px 20px;
        transition: all 0.3s ease-in-out;
        border: none;
    }
    h1, h2, h3 {
        color: #444 !important;
    }
    .st-emotion-cache-6qob1r {
        background: rgba(255, 255, 255, 0.5) !important;
    }
</style>
"""

# Streamlit App Setup
st.set_page_config(page_title="💰 Budget AI Assistant", layout="centered")
st.markdown(page_bg_css, unsafe_allow_html=True)

st.title("💡 Indian Budget Analysis AI Agent")
st.markdown("🚀 Ask me anything about the **Indian Union Budget 2025-26**")

# Synchronous function to fetch URLs
def fetch_url(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return url, response.content
        else:
            st.warning(f"⚠️ Failed to fetch {url}: Status {response.status_code}")
            return url, None
    except Exception as e:
        st.warning(f"⚠️ Error fetching {url}: {str(e)}")
        return url, None

# Function to initialize knowledge bases synchronously
@st.cache_resource(ttl=86400)  # Cache for 24 hours
def initialize_knowledge_bases():
    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.text("🔄 Initializing Vector DB...")
    time.sleep(1)  # Simulate DB setup
    vector_db = LanceDb(
        table_name="budget",
        uri="tmp/lancedb",
        search_type=SearchType.vector,
        embedder=embedder,
    )
    progress_bar.progress(30)
    time.sleep(1)

    status_text.text("📄 Loading Budget Local PDF Documents...")
    time.sleep(1)
    pdf_folder = Path(".")
    pdf_files = [
        pdf_folder / "Union_Budget_FY25-26.pdf"          
    ]
    combined_pdf_kb = []
    for pdf_file in pdf_files:
        pdf_kb = PDFKnowledgeBase(
            path=pdf_file,
            vector_db=LanceDb(
                table_name=f"pdf_{pdf_file.stem}",
                uri="tmp/lancedb",
                search_type=SearchType.vector,
                embedder=embedder,
            ),
            name=f"Indian Budget Local PDF - {pdf_file.stem}",
            instructions=[
                "Prioritize checking the pdf for answers.",
                "Chunk the pdf in a way that preserves context.",
                "Ensure important sections like summaries and conclusions remain intact.",
                "Maintain the integrity of the logical sections if needed.",
                "Each chunk should provide enough information to answer questions independently.",
                "Create self-contained information units that can provide a full answer to a query.",
            ]
        )
        combined_pdf_kb.append(pdf_kb)

    status_text.text("📄 Loading Budget PDF Documents...")
    pdf_urls = [
        "https://www.indiabudget.gov.in/doc/rec/allrec.pdf",
        "https://prsindia.org/files/budget/budget_parliament/2025/Union_Budget_Analysis_2025-26.pdf",
        "https://www.ey.com/content/dam/ey-unified-site/ey-com/en-in/technical/alerts-hub/documents/2025/ey-union-budget-2025-alert-infra-sector.pdf",
        "https://www.indiabudget.gov.in/doc/bh1.pdf",
        "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/feb/doc202524496501.pdf",
        "https://www.indiabudget.gov.in/doc/AFS/allafs.pdf",
        "https://www.indiabudget.gov.in/doc/eb/alldg.pdf",
        "https://www.indiabudget.gov.in/doc/eb/allsbe.pdf",
        "https://www.indiabudget.gov.in/doc/Finance_Bill.pdf",
        "https://www.indiabudget.gov.in/doc/Budget_Speech.pdf",
        "https://www.indiabudget.gov.in/doc/OutcomeBudgetE2025_2026.pdf",
        "https://www.indiabudget.gov.in/doc/memo.pdf",
        "https://www.indiabudget.gov.in/doc/eb/vol1.pdf",
        "https://www.indiabudget.gov.in/doc/frbm1.pdf",
        "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/feb/doc202521492801.pdf",
        "https://www.indiabudget.gov.in/budget2024-25/doc/Key_to_Budget_Document_2024.pdf",
    ]

    results = [fetch_url(url) for url in pdf_urls]
    valid_urls = [url for url, content in results if content is not None]

    pdf_knowledge_base = PDFUrlKnowledgeBase(
        urls=valid_urls,
        vector_db=vector_db,
        name="Indian Budget Records",
        instructions=[
            "For user questions first check the pdf_knowledge_base.",
            "Divide the document into chunks that maintain context around key concepts.",
            "Ensure important sections like summaries and conclusions remain intact.",
            "Each chunk should provide enough information to answer questions independently."
        ]
    )
    progress_bar.progress(60)

    status_text.text("🌍 Fetching Budget Website Data...")
    website_urls = [
        "https://www.india.gov.in/spotlight/union-budget-2025-2026",
        "https://www.bajajfinserv.in/investments/income-tax-slabs",
        "https://www.india.gov.in/spotlight/union-budget-2024-25",
        "https://idronline.org/article/advocacy-government/budget-2025-understanding-social-sector-spending/?gad_source=1&gclid=CjwKCAiAlPu9BhAjEiwA5NDSA8hXbzwy3kj1HhhuaRlFZx4kgbgJsgDrPNIbigkD0WJQaocfzFZSwRoCnkYQAvD_BwE",
        "https://frontline.thehindu.com/news/india-budget-2025-key-announcements-tax-relief-agriculture-healthcare-reforms/article69167699.ece",
        "https://www.moneycontrol.com/budget/budget-2025-speech-highlights-key-announcements-of-nirmala-sitharaman-in-union-budget-of-india-article-12926372.html"
    ]

    website_results = [fetch_url(url) for url in website_urls]
    valid_website_urls = [url for url, content in website_results if content is not None]

    website_knowledge_base = WebsiteKnowledgeBase(
        urls=valid_website_urls,
        vector_db=LanceDb(
            table_name="website_documents",
            uri="tmp/lancedb",
            search_type=SearchType.vector,
            embedder=embedder,
        ),
        max_links=10,
        name="Indian Budget Website",
        instructions=[
            "Focus on extracting information that directly answers user questions about the Indian Union Budget.",
            "Prioritize sections like headlines, key findings, summaries, announcements, and data tables.",
            "Identify and extract specific budget-related data, such as allocations, policy changes, tax reforms, or economic forecasts.",
            "Ignore content that is not directly related to the Indian Union Budget, such as advertisements, site navigation, or unrelated news.",
            "Ensure each extracted piece of information retains its original context and meaning, allowing it to be understood independently.",
            "When extracting data, include any associated explanatory text or context that explains what the data means and where it comes from.",
            "Maintain the logical flow and coherence of extracted content, avoiding fragmented or disconnected sentences.",
            "If a section contains multiple related data points or insights, keep them together as a single coherent unit.",
            "Extract exact information related to the user query."
        ]
    )
    progress_bar.progress(80)

    status_text.text("🔍 Combining Knowledge Bases...")
    combined_knowledge_base = CombinedKnowledgeBase(
        sources=[pdf_knowledge_base, website_knowledge_base] + combined_pdf_kb,
        vector_db=LanceDb(
            table_name="combined_documents",
            uri="tmp/lancedb",
            search_type=SearchType.vector,
            embedder=embedder,
        ),
    )

    time.sleep(1)  # Simulate loading
    combined_knowledge_base.load(recreate=False)

    progress_bar.progress(100)
    status_text.text("✅ Knowledge Base Loaded Successfully!")
    return combined_knowledge_base

# Load knowledge base in session state
if 'combined_knowledge_base' not in st.session_state:
    st.session_state.combined_knowledge_base = initialize_knowledge_bases()

# Initialize Agents (rest of the code remains the same)
knowledge_agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp", api_key=api_key),
    knowledge=st.session_state.combined_knowledge_base,
    search_knowledge=True,
    description="📖 Expert on Indian Budget Documents & Websites",
    instructions=[
        "When answering user questions, first delegate the query to the knowledge base and prioritize checking local PDF documents (e.g.Union Budget FY25-26.pdf) for accurate information.",
        "If the answer is not found in the local PDFs, then check other sources in the knowledge base (e.g., PDF URLs and websites).",
        "If the answer is not found in the knowledge base, automatically use DuckDuckGoTools for further web research.",
        "Present your response in a formal manner with headings like 'Overview', 'Details', 'Conclusion', 'Visualization','Sources & Methodology', 'additional information' etc.",
        "For complex queries, break them down into simpler parts if necessary.",
        "Ensure responses are accurate and reference the document or website explicitly where possible.",
        "Use markdown for formatting responses, including bullet points and tables where appropriate.",
        "If the query seems ambiguous, ask for clarification from the user."
    ]
)

searcher = Agent(
    name="Searcher",
    model=Gemini(id="gemini-2.0-flash-exp", api_key=api_key),
    role="🔎 Web Searcher for Budget Analysis",
    description="Specialist in retrieving and analyzing Indian Budget information.",
    instructions=[
        "Activate only when explicitly delegated a query by the 'budget_agent' after the 'knowledge_agent' fails to provide a sufficient answer from the knowledge base.",
        "First, check if the user answer can be found in the existing knowledge_agent or knowledge base.",
        "Reputable financial news outlets (e.g., Moneycontrol, Economic Times)",
        "Economic think tanks and analyses (e.g., NITI Aayog, IMF).",
        "If the information is not available in the knowledge_agent or knowledge base, automatically initiate a web search using DuckDuckGoTools.",
        "Prioritize Indian financial news, government websites, and international news discussing India's budget.",
        "Search specifically for documents or articles related to the Indian Union Budget, focusing on official sources from the government, reputable financial news, and analysis platforms.",
        "When searching, use keywords like 'Indian Budget Analysis', 'Union Budget India', 'Budget 2025-2026 India', along with any specific terms from the query to refine the search.",
        "Compile the results, summarizing key points in your response.",
        "Focus on time-sensitive information related to budget announcements and their immediate global impact.",
        "Maintain objectivity with a focus on data from economic think tanks and financial analysts.",
        "Ensure that the response includes an 'Overview', 'Details' section for in-depth information, and a 'Conclusion' or 'Summary'.",
        "Use markdown for formatting responses, incorporating bullet points for clarity and tables where data comparison is needed.",
        "If the query is ambiguous or requires further clarification, ask for more details from the user.",
        "Keep responses formal and precise, always citing or referencing the source of information when possible.",
        "Use bullet points for clarity."
        "**📈 Data Visualization** (if applicable)"
        "**Table**: For numerical comparisons, e.g."
    ],
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    search_knowledge=True,
)

budget_agent = Agent(
    name="Budget Analysis Agent",
    model=Gemini(id="gemini-2.0-flash-exp", api_key=api_key),
    team=[knowledge_agent, searcher],
    description=dedent("""\
        🤖 An expert analyst team dedicated to analyzing and providing insights on the Indian Budget. 
        This agent leverages pre-existing knowledge from official documents from the knowledge base or current web-based information to deliver comprehensive budget analysis. 
        It works in tandem with a knowledge agent for document-based queries and a searcher agent for the latest updates and analyses from the web.
        If no data found in the Knowledge agent Automatically run the searcher agent.
    """),
    instructions=dedent("""\
        - Start by delegating the user’s query to the 'knowledge_agent' to search the existing knowledge base, which contains official budget documents and trusted website data.
        - Wait for the 'knowledge_agent' to provide a response before taking any further action.
        - Begin by delegating the query to the 'knowledge_agent' to check for any relevant information in the existing knowledge bases.
        - Do not run the 'searcher' agent unless the 'knowledge_agent' explicitly fails to provide a sufficient answer, as defined above.
        - If the 'knowledge_agent' does not respond or no answer, automatically delegate the task to the 'searcher' agent to perform a web search.
        - For both agents, ensure searches are tailored with keywords like 'Indian Budget', 'Union Budget India', 'Budget Analysis', and any query-specific terms.
        - Key viewpoints from budget speeches, financial reviews, and economic think tanks.
        - If the response from knowledge_agent is empty or inadequate, **run the searcher**.
        - Stakeholder reactions: Include responses from industry bodies/opposition.
        - Format the response with clear headings:
          - **📌 Overview**: A brief summary of the budget point in question.
          - **📊 Details**: In-depth analysis, including any numerical data, policy implications, or sector-specific impacts.
          - **✅ Conclusion**: Summarize key takeaways, expected outcomes, or areas for further research.
          -- **Numerical Data**: Tables or figures for budgetary allocations and expenditures.
          -- **Sources**: Cite documents or URLs where applicable.
        - Comparisons with previous budgets for trend analysis.
        - Use markdown for formatting outputs, including bullet points, tables, or code blocks for clarity.
        - If the query lacks clarity, prompt the user for additional details or clarification.
        - Maintain a formal and professional tone in responses, always citing sources where applicable.
        - Use bullet points for clarity.
        
    """),
    expected_output=dedent("""\
        # {Compelling Headline}                   
        ### Overview
        - Here's a brief summary of the budget analysis for the query.
        ### Details
        - Detailed breakdown including numbers, policies, and sector analysis.
        ## Expert Insights
        - Quotes from economists and market analysts
        ## Numerical Breakdown
        - Create comparative tables for allocations:
            | Sector | 2024-25 | 2025-26 | Change (%) |
            |--------|---------|---------|------------|
            | Health | 89,000cr| 1,05,000cr | +18%     |
        ## Geographic Distribution
        - State-wise fund allocation patterns
        - Special focus regions/aspirational districts
        Always include:
        - Reference to specific document/page numbers
        - Source URLs for web-sourced information
        - Last updated timestamps for time-sensitive data                           
        ## Sources & Methodology
        - Description of research process and sources
        - page number of pdfs and source page name and file name
        - website urls list 
        ## For technical queries:
        - Create flowchart for complex processes
        - Use code blocks for formula explanations
        - Add footnotes for legal citations        
                                                                                                    
        ### Conclusion
        - Key insights and implications from the budget analysis.
        - Suggested compliance strategies.
                           
        ### Visualization
        - "**📈 Data Visualization** (if applicable):"
        - "**Table**: For numerical comparisons, "
        - Include tables/pie charts when data is sufficient (3+ points) and relevant.
        ---
        Research conducted by Financial Agent
        Credit Rating Style Report
        Published: {current_date}
        Last Updated: {current_time}                                                    
    """),
    add_datetime_to_instructions=True,
    markdown=True,
    show_tool_calls=True,
)

# Streamlit UI for User Input
query = st.text_input("🔍 Enter your budget-related query:", placeholder="E.g., What are the major tax changes in Budget 2025?")

# Custom Button CSS
button_css = """
    <style>
        .stButton > button {
            background-color: #008CBA;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            transition: 0.3s;
        }
        .stButton > button:hover {
            background-color: #005F73;
            color: #FFD700;
        }
    </style>
"""
st.markdown(button_css, unsafe_allow_html=True)

# Button to Generate Response
if st.button("🚀 Generate Response"):
    if query:
        with st.spinner("📊 Analyzing budget data... Please wait."):
            try:
                run_response = budget_agent.run(query, markdown=True)
                st.markdown(run_response.content, unsafe_allow_html=True)
                # Check for pie chart data in response
                pie_chart_match = re.search(r"Pie Chart:.*?(?=###|\n\n|$)", run_response.content, re.DOTALL)
                if pie_chart_match:
                    pie_text = pie_chart_match.group()
                    labels = []
                    values = []
                    for line in pie_text.split("\n")[1:]:
                        if line.strip().startswith("-"):
                            label, value = line.split(":")
                            labels.append(label.strip("- ").strip())
                            values.append(float(value.strip().replace("%", "")))
                    fig = px.pie(values=values, names=labels, title="Budget Allocation")
                    st.plotly_chart(fig)
            except Exception as e:
                st.error(f"⚠️ An error occurred: {str(e)}. Please try again or contact support.")
    else:
        st.warning("⚠️ Please enter a query before generating a response!")

# Sidebar Info
st.sidebar.header("ℹ️ About")
st.sidebar.markdown("""
🔹 This AI assistant provides **real-time** insights on the Indian **Union Budget 2025-26**  
🔹 Sources: **Government Budget Documents** 📄 + **Trusted Financial Websites** 🌐  
🔹 Uses **AI-powered Agents** 🤖 for **document-based** & **web-based research**
""")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ How It Works")
st.sidebar.markdown("""
1️⃣ **Knowledge Base Search** 📚  
2️⃣ **Web Search (if needed)** 🌍  
3️⃣ **Formatted AI Response** 📊  
""")

st.sidebar.subheader("💡 Example Queries")
st.sidebar.markdown("""
- What are the major tax changes in Budget 2025?
- How much is allocated to healthcare in 2025-26?
- What are the key highlights of the Budget Speech?
""")

st.sidebar.markdown("---")
st.sidebar.subheader("📞 Contact")
st.sidebar.markdown("💡 Created by: **AI & Finance Enthusiasts**")
st.sidebar.markdown("📩 Email: narendra.insights@gmail.com")

# Footer
st.markdown("---")
st.markdown(
    "🛠️ **Built with AI ** | 📅 *Updated: 2025* | "
    "[<img src='https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Bug.svg.original.svg' width='20' height='20'>](https://www.linkedin.com/in/nk-analytics/)"
    " Connect on LinkedIn",
    unsafe_allow_html=True,
)
