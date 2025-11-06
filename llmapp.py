from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
import os
import sqlite3
import pandas as pd  # Used for better data display and schema handling

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Database Functions ---

def get_db_schema(db_path):
    """Connects to the SQLite DB and introspects its schema."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            schema_description = "The database has the following tables:\n"
            
            # Get columns for each table
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [col[1] for col in cursor.fetchall()] # col[1] is the column name
                schema_description += f"\nTable '{table}' has columns: {', '.join(columns)}\n"
                
            return schema_description
    except sqlite3.Error as e:
        st.error(f"Error reading database schema: {e}")
        return None

def execute_sql_query(query, db_path):
    """Executes a SQL query and returns results as a DataFrame."""
    try:
        with sqlite3.connect(db_path) as conn:
            # Use pandas to read sql, which handles column names automatically
            df = pd.read_sql_query(query, conn)
            return df, None  # Return (data, no_error)
    except sqlite3.OperationalError as e:
        return None, f"SQL Error: {e}" # Return (no_data, error_message)
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

# --- Gemini AI Function ---

def get_gemini_response(chat_history, schema_prompt):
    """Generates a response from the Gemini model."""
    
    # NOTE: Using gemini-1.5-pro, as 2.5 is not yet widely available.
    # Adjust "gemini-1.5-pro-latest" to your available model if needed.
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    # Construct the full prompt, including the dynamic schema
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
    
    # Add the chat history to the prompt
    full_prompt.extend(chat_history)
    
    try:
        response = model.generate_content(full_prompt)
        sql_query = response.text.strip()
        
        # A simple cleanup in case the model still adds markdown
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
            
        return sql_query
    except Exception as e:
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
        # Save the uploaded file to a temporary location
        db_path = f"./{uploaded_file.name}"
        with open(db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state.db_path = db_path
        st.success(f"Database '{uploaded_file.name}' loaded!")

        # Get and display schema
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

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past chat messages

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])

        else:  # Assistant
            content = message["content"]

            # Check if it's our new structured content

            if isinstance(content, dict) and "sql" in content:
                with st.expander("View Generated SQL Query"):
                    st.code(content["sql"], language='sql')

                if content["data"] is not None:
                    st.dataframe(content["data"])

                if content["error"] is not None:
                    st.error(content["error"])
            else:

                # Fallback for simple string messages (e.g., "Failed to generate query")
                st.markdown(content)

# Check if DB is ready before showing chat input
if "db_path" not in st.session_state:
    st.info("Please upload a SQLite database in the sidebar to begin.")
else:
    # Get new user question
    if prompt := st.chat_input("Ask a question about your database..."):
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                # Create history list for Gemini
                chat_history_for_api = []

                for m in st.session_state.messages:
                    if m['role'] == 'user':
                        chat_history_for_api.append(f"User: {m['content']}")
                    else: # Assistant
                        content = m['content']
                        if isinstance(content, dict) and "sql" in content:

                            # Add the *SQL query* as the assistant's previous response
                            chat_history_for_api.append(f"Assistant: {content['sql']}")

                        else:
                            chat_history_for_api.append(f"Assistant: {content}")
                # Get the SQL query
                sql_query = get_gemini_response(chat_history_for_api, st.session_state.schema_prompt)
                if sql_query:
                    # Display the generated SQL query in an expander
                    with st.expander("View Generated SQL Query"):
                        st.code(sql_query, language='sql')
                    
                    # Execute the query
                    results_df, error = execute_sql_query(sql_query, st.session_state.db_path)

                    #Save the *entire* structured response to history
                    assistant_message = {
                        "sql": sql_query,
                        "data": results_df,  # Will be None if error
                        "error": error       # Will be None if success

                    }

                    # Display the current result
                    
                    if error:
                        # Show SQL error
                        st.error(error)
                        st.session_state.messages.append({"role": "assistant", "content": error})
                    else:
                        # Show results table
                        st.dataframe(results_df)

                        # Save the structured message to history

                        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                        
                else:
                    st.error("Failed to generate SQL query.")
                    st.session_state.messages.append({"role": "assistant", "content": "Failed to generate SQL query."})