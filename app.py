import streamlit as st
import google.generativeai as genai
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
import tempfile  # <-- IMPORT THIS

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# --- Database Functions ---

def get_db_schema(db_path):
    """Connects to the SQLite DB and introspects its schema."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            schema_description = "The database has the following tables:\n"
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [col[1] for col in cursor.fetchall()]
                schema_description += f"\nTable '{table}' has columns: {', '.join(columns)}\n"
            return schema_description
    except sqlite3.Error as e:
        st.error(f"Error reading database schema: {e}")
        return None

def execute_sql_query(query, db_path):
    """Executes a SQL query and returns results as a DataFrame."""
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df, None
    except sqlite3.OperationalError as e:
        return None, f"SQL Error: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

# --- Gemini AI Function ---

def get_gemini_response(chat_history, schema_prompt):
    """Generates a response from the Gemini model."""
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        full_prompt = [
            f"""You are an expert SQL query generator. Your task is to convert English natural language questions into SQL queries.
            You must only respond with a single, valid SQL query.
            Do not include ```sql in the beginning or ``` at the end.
            Do not include the word 'SQL' in your output.
            
            The SQL database schema is as follows:
            {schema_prompt}
            
            Based on the chat history and the schema, generate the SQL query for the user's latest question.
            """
        ]
        full_prompt.extend(chat_history)
        
        response = model.generate_content(full_prompt)
        sql_query = response.text.strip().replace("```sql", "").replace("```", "")
        return sql_query
    except Exception as e:
        # Handle potential API key errors
        if "API_KEY_INVALID" in str(e):
            st.error("Error: The Google API Key is invalid or not set. Please check your Hugging Face Space secrets.")
            return None
        st.error(f"Error calling Gemini API: {e}")
        return None

# --- Streamlit App UI ---

st.set_page_config(page_title="Dynamic Text-to-SQL", page_icon="🛢️", layout="wide")
st.title("🤖 Gemini SQL Query Generator")
st.markdown("Upload your own SQLite database and ask questions in plain English!")

# --- Sidebar for Database Upload ---
with st.sidebar:
    st.header("Database Setup")
    uploaded_file = st.file_uploader("Upload your SQLite database (.db, .sqlite, .sqlite3)", type=["db", "sqlite", "sqlite3"])

    if uploaded_file:
        # ### THIS IS THE CRITICAL CHANGE ###
        # Create a temporary file to store the uploaded DB
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            db_path = tmp_file.name  # Get the path to the temporary file
        
        st.session_state.db_path = db_path
        st.success(f"Database '{uploaded_file.name}' loaded!")

        with st.spinner("Inspecting database schema..."):
            schema_info = get_db_schema(db_path)
            if schema_info:
                st.session_state.schema_prompt = schema_info
                with st.expander("View Database Schema"):
                    st.text(schema_info)
    
    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.success("Chat history cleared!")

# --- Main Chat Interface ---

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            content = message["content"]
            if isinstance(content, dict) and "sql" in content:
                with st.expander("View Generated SQL Query"):
                    st.code(content["sql"], language='sql')
                if content["data"] is not None:
                    st.dataframe(content["data"])
                if content["error"] is not None:
                    st.error(content["error"])
            else:
                st.markdown(content)

# Check if API key is loaded before showing chat
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY is not set. Please add it to your Hugging Face Space secrets.")
elif "db_path" not in st.session_state:
    st.info("Please upload a SQLite database in the sidebar to begin.")
else:
    if prompt := st.chat_input("Ask a question about your database..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                chat_history_for_api = []
                for m in st.session_state.messages:
                    if m['role'] == 'user':
                        chat_history_for_api.append(f"User: {m['content']}")
                    else:
                        content = m['content']
                        if isinstance(content, dict) and "sql" in content:
                            chat_history_for_api.append(f"Assistant: {content['sql']}")
                        else:
                            chat_history_for_api.append(f"Assistant: {content}")
                
                sql_query = get_gemini_response(chat_history_for_api, st.session_state.schema_prompt)
                
                if sql_query:
                    with st.expander("View Generated SQL Query"):
                        st.code(sql_query, language='sql')

                    results_df, error = execute_sql_query(sql_query, st.session_state.db_path)
                    
                    assistant_message = {
                        "sql": sql_query,
                        "data": results_df,
                        "error": error
                    }
                    
                    if error:
                        st.error(error)
                    else:
                        st.dataframe(results_df)
                    
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                else:
                    st.error("Failed to generate SQL query.")
                    st.session_state.messages.append({"role": "assistant", "content": "Failed to generate SQL query."})