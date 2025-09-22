import os
import streamlit as st
from strands import Agent
from strands.models import BedrockModel
from strands_tools import use_llm, memory

# Import the specialized assistants
from computer_science_assistant import computer_science_assistant
from english_assistant import english_assistant
from language_assistant import language_assistant
from math_assistant import math_assistant
from no_expertise import general_assistant

# Define the teacher's assistant system prompt
TEACHER_SYSTEM_PROMPT = """
You are TeachAssist, a sophisticated educational orchestrator designed to coordinate educational support across multiple subjects. Your role is to:

1. Analyze incoming student queries and determine the most appropriate specialized agent to handle them:
   - Math Agent: For mathematical calculations, problems, and concepts
   - English Agent: For writing, grammar, literature, and composition
   - Language Agent: For translation and language-related queries
   - Computer Science Agent: For programming, algorithms, data structures, and code execution
   - General Assistant: For all other topics outside these specialized domains

2. Key Responsibilities:
   - Accurately classify student queries by subject area
   - Route requests to the appropriate specialized agent
   - Maintain context and coordinate multi-step problems
   - Ensure cohesive responses when multiple agents are needed

3. Decision Protocol:
   - If query involves calculations/numbers → Math Agent
   - If query involves writing/literature/grammar → English Agent
   - If query involves translation → Language Agent
   - If query involves programming/coding/algorithms/computer science → Computer Science Agent
   - If query is outside these specialized areas → General Assistant
   - For complex queries, coordinate multiple agents as needed

Always confirm your understanding before routing to ensure accurate assistance.
"""

ACTION_SYSTEM_PROMPT = """
You route queries to either a Teacher agent or a Knowledge Base agent.

Output EXACTLY one word: "teacher" or "knowledgebase".

Send to knowledgebase only if the user intent is clearly about storing or recalling personal facts or prior saved info, e.g.:
- remember/save/store/record/note that ...
- my name is / I live in / my birthday is ...
- what did I tell you / what do you remember about ...
- retrieve/recall my ...

Otherwise, send to teacher for subject-matter questions (math, programming, grammar, translation, general questions).
Do not add explanations.
"""

KB_ACTION_SYSTEM_PROMPT = """
You are a knowledge base assistant focusing ONLY on classifying user queries.
Your task is to determine whether a user query requires STORING information to a knowledge base
or RETRIEVING information from a knowledge base.

Reply with EXACTLY ONE WORD - either "store" or "retrieve".
"""

ANSWER_SYSTEM_PROMPT = """
You are a helpful knowledge assistant that provides clear, concise answers 
based on information retrieved from a knowledge base.

The information from the knowledge base contains document IDs, titles, 
content previews and relevance scores. Focus on the actual content and 
ignore the metadata.
"""

# Ensure Knowledge Base ID handling (fallback for demos) and allow runtime override
DEFAULT_KB_ID = "demokb123"
kb_env_key = "STRANDS_KNOWLEDGE_BASE_ID"

def get_current_kb_id() -> str:
    kb_id = os.environ.get(kb_env_key) or DEFAULT_KB_ID
    if not os.environ.get(kb_env_key):
        st.warning(
            "STRANDS_KNOWLEDGE_BASE_ID is not set. Using demo knowledge base. "
            "Set the environment variable for real data: export STRANDS_KNOWLEDGE_BASE_ID=<your_kb_id>"
        )
    return kb_id

def is_valid_kb_id(kb_id: str) -> bool:
    # Strands memory expects an alphanumeric ID (no hyphens or special chars)
    return isinstance(kb_id, str) and kb_id.isalnum() and len(kb_id) >= 6

# Set up the page
st.set_page_config(page_title="TeachAssist - Educational Assistant", layout="wide")
st.title("TeachAssist - Educational Assistant")
st.write("Ask a question in any subject area or store/retrieve personal information.")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialize the teacher agent
@st.cache_resource
def get_teacher_agent():
    # Specify the Bedrock ModelID
    bedrock_model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        temperature=0.3,
    )
    
    # Create the teacher agent with specialized tools
    return Agent(
        model=bedrock_model,
        system_prompt=TEACHER_SYSTEM_PROMPT,
        callback_handler=None,
        tools=[math_assistant, language_assistant, english_assistant, computer_science_assistant, general_assistant],
    )

@st.cache_resource
def get_kb_agent(kb_id: str):
    bedrock_model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        temperature=0.3,
    )
    # Ensure the env var is set for tools that read it
    os.environ[kb_env_key] = kb_id
    return Agent(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        tools=[memory, use_llm],
    )

def _looks_like_kb_query(query: str) -> bool:
    text = (query or "").lower()
    kb_keywords = [
        "remember", "store", "save", "record", "note that",
        "what did i tell", "what do you remember", "recall", "retrieve",
        "my name is", "i live", "my birthday", "where do i live", "who am i"
    ]
    return any(k in text for k in kb_keywords)

def _normalize_store_content(raw: str) -> str:
    text = (raw or "").strip()
    lower = text.lower()
    prefixes = [
        "remember that ",
        "remember ",
        "save that ",
        "save ",
        "store that ",
        "store ",
        "note that ",
        "record that ",
    ]
    for p in prefixes:
        if lower.startswith(p):
            # Remove the prefix using original text length for proper casing
            return text[len(p):].strip()
    return text

# Re-added helpers for parsing/summarizing memory retrievals
def _extract_memory_entries(raw_results: str):
    entries = []
    if not raw_results:
        return entries
    lines = raw_results.splitlines()
    for line in lines:
        if "Content Preview:" in line:
            snippet = line.split("Content Preview:", 1)[1].strip()
            # Prefer extracting the content field from JSON-ish previews
            if '"content":' in snippet:
                part = snippet.split('"content":', 1)[1].lstrip()
                if part.startswith('"'):
                    part = part[1:]
                end = part.find('"')
                if end > -1:
                    entries.append(part[:end].strip())
                    continue
            if snippet:
                entries.append(snippet)
    return entries

def _answer_from_memory(query: str, memories):
    q = (query or "").lower()
    blob = "\n".join(memories)
    import re
    if "birthday" in q:
        m = re.search(r"birthday\s+is\s+([^\n\"\.]+)", blob, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Normalize common misspelling 'oktober' -> 'october'
            val = val.replace("oktober", "october")
            return f"Your birthday is {val}."
    if "where do i live" in q or "where i live" in q:
        m = re.search(r"i\s+live\s+in\s+([^\n\"\.]+)", blob, re.IGNORECASE)
        if m:
            return f"You live in {m.group(1).strip()}."
    if "my name" in q:
        m = re.search(r"my\s+name\s+is\s+([^\n\"\.]+)", blob, re.IGNORECASE)
        if m:
            return f"Your name is {m.group(1).strip()}."
    return None

def determine_action(query):
    """Determine if the query should be handled by the teacher agent or knowledge base agent"""
    # Heuristic first: default to teacher unless it's clearly a memory action
    if _looks_like_kb_query(query):
        return "knowledgebase"

    # Fallback to LLM routing if ambiguous
    agent = get_kb_agent(get_current_kb_id())
    result = agent.tool.use_llm(
        prompt=f"Query: {query}",
        system_prompt=ACTION_SYSTEM_PROMPT
    )

    action_text = str(result).lower().strip()
    return "knowledgebase" if action_text == "knowledgebase" else "teacher"

def run_kb_agent(query):
    """Process a user query with the knowledge base agent"""
    kb_id = get_current_kb_id()
    if not is_valid_kb_id(kb_id):
        return (
            "Knowledge base is not configured. Provide a valid alphanumeric Knowledge Base ID "
            f"(no hyphens or special characters, got '{kb_id}')."
        )
    agent = get_kb_agent(kb_id)
   
    result = agent.tool.use_llm(
        prompt=f"Query: {query}",
        system_prompt=KB_ACTION_SYSTEM_PROMPT
    )

    action_text = str(result).lower().strip()
    if "store" in action_text:
        normalized = _normalize_store_content(query)
        agent.tool.memory(action="store", content=normalized or query)
        return "I've stored this information."
    else:
        result = agent.tool.memory(
            action="retrieve",
            query=query,
            min_score=float(st.session_state.get("kb_min_score", 0.6)),
            max_results=int(st.session_state.get("kb_max_results", 5)),
        )
        result_str = str(result)
        # Provide a clearer hint if KB is misconfigured
        if ("status': 'error'" in result_str) or ("\"status\": \"error\"" in result_str) or ('No knowledge base ID' in result_str):
            return (
                "Knowledge base request failed. Please verify the ID, region, and permissions. "
                f"Current ID: {kb_id}. Error: {result_str}"
            )
        if "No results found" in result_str:
            return (
                "I don't have any stored information matching that yet. "
                "Try phrasing a fact to store first, e.g. 'Remember that my birthday is 12 Oct'."
            )
        # Filter to memory entries and try direct answer
        memories = _extract_memory_entries(result_str)
        direct = _answer_from_memory(query, memories)
        if direct:
            return direct
        # As a fallback, summarize only memory entries to keep output clean
        if memories:
            summary = agent.tool.use_llm(
                prompt=(
                    "User question: \n" + query + "\n\n" +
                    "Relevant stored facts: \n- " + "\n- ".join(memories) +
                    "\n\nAnswer succinctly based only on these facts. If unknown, say you don't have that info."
                ),
                system_prompt=ANSWER_SYSTEM_PROMPT,
            )
            return str(summary)
        return "I couldn't extract any relevant stored facts yet. Try storing it explicitly, e.g. 'Remember that my birthday is 12 Oct'."
    return result

# Sidebar controls for KB configuration visibility/override
with st.sidebar:
    st.subheader("Knowledge Base Settings")
    current_id = get_current_kb_id()
    kb_id_input = st.text_input("STRANDS_KNOWLEDGE_BASE_ID", value=current_id)
    if kb_id_input and kb_id_input != os.environ.get(kb_env_key):
        os.environ[kb_env_key] = kb_id_input
        st.success("Knowledge Base ID updated for this session.")
    # Retrieval tuning controls
    if "kb_min_score" not in st.session_state:
        st.session_state.kb_min_score = 0.6
    if "kb_max_results" not in st.session_state:
        st.session_state.kb_max_results = 5
    st.session_state.kb_min_score = st.slider(
        "KB min score (filter)", min_value=0.0, max_value=1.0, value=st.session_state.kb_min_score, step=0.05
    )
    st.session_state.kb_max_results = st.number_input(
        "KB max results", min_value=1, max_value=50, value=st.session_state.kb_max_results, step=1
    )

# Get user input
query = st.chat_input("Ask your question here...")

if query:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(query)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            with st.spinner("Analyzing query..."):
                action = determine_action(query)

            content = ""
                    
            if (action == "teacher"): 
                # Get the teacher agent
                teacher_agent = get_teacher_agent()
                
                # Process the query
                with st.spinner("Thinking..."):
                    response = teacher_agent(query)
                    content = str(response)
            else:
                # Process the query
                with st.spinner("Accessing knowledge base..."):
                    content = run_kb_agent(query)
            
            # Display the response
            message_placeholder.markdown(content)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": content})
            
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            message_placeholder.markdown(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})