import streamlit as st
from dotenv import load_dotenv
import os
import time
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.lancedb import LanceDb
from agno.embedder.google import GeminiEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.document.chunking.document import DocumentChunking
from agno.models.google import Gemini
from textwrap import dedent
from agno.vectordb.search import SearchType

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

embedder = GeminiEmbedder(id="models/text-embedding-004", dimensions=768,api_key=api_key)

#chunking_strategy = DocumentChunking(chunk_size=5000, overlap=0)
# 🎨 Custom CSS for gradient background (PLACE THIS AT THE BEGINNING)
page_bg_css = """
<style>
    /* Background Gradient */
    html, body, [class*="css"]  {
        min-height: 100vh;
        background: linear-gradient(to right, #f7f9fc, #ddeeff);
        color: white;
    }

    /* Main content container */
    .stApp {
        background: transparent;
        min-height: 100vh;
    }

    /* Input fields and buttons */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea, 
    .stButton>button {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: #333 !important; /* Dark Gray Text */
        border: 1px solid #aaccee !important; /* Soft Blue Border */
        border-radius: 10px; /* Rounded Corners */
    }

    /* Button hover effect */
    .stButton>button:hover {
        background-color: #aaccee !important; /* Soft Blue */
        color: #333 !important; /* Darker Text */
        border-radius: 12px;
        font-size: 16px;
        padding: 10px 20px;
        transition: all 0.3s ease-in-out;
        border: none;
    }

    /* Headers */
    h1, h2, h3 {
        color: #444 !important;
    }

    /* Sidebar */
    .st-emotion-cache-6qob1r {
        background: rgba(255, 255, 255, 0.5) !important; /* Light Transparent Sidebar */
    }
</style>
"""

# Streamlit App Title and UI
st.set_page_config(page_title="💰 Budget AI Assistant", layout="centered")


# ✅ Inject CSS before any UI elements
st.markdown(page_bg_css, unsafe_allow_html=True)

st.title("💡 Indian Budget Analysis AI")

st.markdown("🚀 Ask me anything about the **Indian Union Budget 2025-26**")

# Function to initialize knowledge bases (Runs only once per session)
@st.cache_resource
def initialize_knowledge_bases():
    progress_bar = st.progress(0)
    status_text = st.empty()  # To show loading messages

    status_text.text("🔄 Initializing Vector DB...")
    time.sleep(1)
    vector_db = LanceDb(
        table_name="budget",
        uri="tmp/lancedb",
        search_type=SearchType.vector,
        embedder=embedder,
    )

    progress_bar.progress(30)
    status_text.text("📄 Loading Budget PDF Documents...")
    time.sleep(1)

    pdf_knowledge_base = PDFUrlKnowledgeBase(
        urls=[
            "https://www.indiabudget.gov.in/doc/rec/allrec.pdf",
            "https://www.indiabudget.gov.in/doc/bh1.pdf",
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
        ],
        vector_db=vector_db,
        #chunking_strategy=chunking_strategy,
        name="Indian Budget Records",
        instructions=[
            "Divide the document into chunks that maintain context around key concepts.",
            "Ensure important sections like summaries and conclusions remain intact.",
            "Each chunk should provide enough information to answer questions independently."
        ]
    )

    progress_bar.progress(60)

    status_text.text("🌍 Fetching Budget Website Data...")
    time.sleep(1)

    website_knowledge_base = WebsiteKnowledgeBase(
        urls=[
            "https://www.india.gov.in/spotlight/union-budget-2025-2026",
            "https://www.india.gov.in/spotlight/union-budget-2024-25",
            "https://www.moneycontrol.com/budget/budget-2025-speech-highlights-key-announcements-of-nirmala-sitharaman-in-union-budget-of-india-article-12926372.html"
        ],
        vector_db=LanceDb(
            table_name="website_documents",
            uri="tmp/lancedb",
            search_type=SearchType.vector,
            embedder=embedder,
        ),
        #chunking_strategy=chunking_strategy, 
        max_links=10,
        name="Indian Budget Website",
        instructions=[
            "Extract relevant information about budget announcements, policies, and updates.",
            "Ensure the context of each piece of information is preserved to answer queries effectively."
            "Ensure that each extracted section preserves its original context."
        ]
    )

    combined_knowledge_base = CombinedKnowledgeBase(
        sources=[pdf_knowledge_base, website_knowledge_base],
        vector_db=LanceDb(
            table_name="combined_documents",
            uri="tmp/lancedb",
            search_type=SearchType.vector,
            embedder=embedder,
        ),
    )

    combined_knowledge_base.load(recreate=False)

    progress_bar.progress(100)
    status_text.text("🔍 Indexing Data into Knowledge Base...")
    time.sleep(1)
    st.success("✅ Knowledge Base Loaded Successfully!")
    return combined_knowledge_base

# Load knowledge base in session state
if 'combined_knowledge_base' not in st.session_state:
    st.session_state.combined_knowledge_base = initialize_knowledge_bases()

# Initialize Agents
#gemini_model = Gemini(id="gemini-2.0-flash-exp", api_key=api_key)

knowledge_agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp", api_key=api_key),
    knowledge=st.session_state.combined_knowledge_base,
    search_knowledge=True,
    description="📖 Expert on Indian Budget Documents & Websites",
    instructions=[
        "When answering questions, first check the knowledge base for accurate information.",
        "If the answer is not found in the knowledge base, automatically use DuckDuckGoTools for further research.",
        "Present your response in a formal manner with headings like 'Overview', 'Details', 'Conclusion', etc.",
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
        "First, check if the answer can be found in the existing knowledge base.",
        "If the information is not available in the knowledge base, automatically initiate a web search using DuckDuckGoTools.",
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
        🤖 An expert analyst team  dedicated to analyzing and providing insights on the Indian Budget. 
        This agent leverages  of pre-existing knowledge from official documents from the knowledge base or current web-based information to deliver comprehensive budget analysis. 
        It works in tandem with a knowledge agent for document-based queries and a searcher agent for the latest updates and analyses from the web.
        If no data found in the Knowledge agent Automatically run the searcher agent.
    """),
    instructions=dedent("""\
        - Begin by delegating the query to the 'knowledge_agent' to check for any relevant information in the existing knowledge bases.
        - If the 'knowledge_agent' does not respond or no answer,automatically delegate the task to the 'searcher' agent to perform a web search.
        - For both agents, ensure searches are tailored with keywords like 'Indian Budget', 'Union Budget India', 'Budget Analysis', and any query-specific terms.
        - Key viewpoints from budget speeches, financial reviews, and economic think tanks.
        - If the response from knowledge_agent is empty or inadequate, **run the searcher**.
        -  Stakeholder reactions: Include responses from industry bodies/opposition.
        #- Combine the findings from both agents, prioritizing information from official documents but also including recent web-based insights for a holistic view.
        - Format the response with clear headings:
          - ** 📌Overview**: A brief summary of the budget point in question.
          - **📊 Details**: In-depth analysis, including any numerical data, policy implications, or sector-specific impacts.
          - **✅ Conclusion**: Summarize key takeaways, expected outcomes, or areas for further research.
          -- ** Numerical Data: Tables or figures for budgetary allocations and expenditures.
        - Comparisons with previous budgets for trend analysis.
        - Use markdown for formatting outputs, including bullet points, tables, or code blocks for clarity.
        - If the query lacks clarity, prompt the user for additional details or clarification.
        - Maintain a formal and professional tone in responses, always citing sources where applicable.
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

        ## For technical queries:
        - Create flowchart for complex processes
        - Use code blocks for formula explanations
        - Add footnotes for legal citations                                                                                 

        ### Conclusion
        - Key insights and implications from the budget analysis.
        - Suggested compliance strategies.
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

# ✅ **Custom Hover Button CSS**
button_css = """
    <style>
        .stButton > button {
            background-color: #008CBA;  /* Blue Color */
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            transition: 0.3s;
        }
        .stButton > button:hover {
            background-color: #005F73;  /* Darker Blue on Hover */
            color: #FFD700;  /* Gold Text on Hover */
        }
    </style>
"""
st.markdown(button_css, unsafe_allow_html=True)

# **Button to Generate Response**
if st.button("🚀 Generate Response"):
    if query:
        with st.spinner("📊 Analyzing budget data... Please wait."):
            run_response = budget_agent.run(query, markdown=True)  
            response_content = run_response.content  
            st.markdown(response_content, unsafe_allow_html=True)

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

st.sidebar.markdown("---")

st.sidebar.subheader("📞 Contact")
st.sidebar.markdown("💡 Created by: **AI & Finance Enthusiasts**")
st.sidebar.markdown("📩 Email: narendra.insights@gmail.com")

# Footer
st.markdown("---")
st.markdown("🛠️ **Built with AI & Love ❤️** | 📅 *Updated: 2025*")

