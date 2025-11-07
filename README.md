# 🤖 Text-to-SQL with Gemini & Streamlit

This project is an intelligent "Chat with your Database" application. It uses Google's Gemini 2.5 Pro to convert natural language (plain English) questions into SQL queries, which are then executed against a user-uploaded SQLite database.

The app is built with Streamlit and deployed on Hugging Face Spaces.

[![Run on Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue?style=for-the-badge&logo=huggingface)](https://huggingface.co/spaces/[YOUR_USERNAME]/[YOUR_SPACE_NAME])
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51.0-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)

## 🚀 Live Demo

Here is a brief demonstration of the app's capabilities:

[![Run Text-to-SQL Demo on HuggingFace Spaces)](https://huggingface.co/spaces/pandaaaboy/Text-to-SQL-Gemini2.5Pro)]
![Demo](https://github.com/anirud25/Text-to-SQL-LLM-Application/blob/master/Demo2.PNG)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [How It Works](#-how-it-works)
- [Local Installation](#-local-installation)
- [Deployment to Hugging Face](#-deployment-to-hugging-face)
  - [File Structure](#file-structure)
  - [Hugging Face Secrets](#hugging-face-secrets)
  - [Troubleshooting: 403 Error Fix](#troubleshooting-403-error-fix)
- [Future Improvements](#-future-improvements)

---

## ✨ Features

* **Natural Language to SQL:** Ask questions like "How many students are in 10th Grade?" instead of writing `SELECT COUNT(*) FROM students WHERE CLASS='10th Grade';`.
* **Dynamic DB Upload:** Upload any `.db`, `.sqlite`, or `.sqlite3` database file.
* **Automatic Schema Detection:** The app automatically inspects the uploaded database's schema (tables and columns).
* **Dynamic Prompt Engineering:** The database schema is injected into the Gemini prompt in real-time, giving the AI the context it needs to write accurate queries.
* **Chat History:** The app maintains a session state, allowing you to ask follow-up questions.
* **Robust Error Handling:** If the generated SQL is invalid, the app displays the database error instead of crashing.
* **Dataframe Display:** Results are shown in a clean, scrollable `st.dataframe`.

---

## 🛠️ Tech Stack

* **Language:** Python
* **Generative AI:** Google Gemini Pro (`google-generativeai`)
* **Web Framework:** Streamlit
* **Data Handling:** Pandas, SQLite3
* **Deployment:** Hugging Face Spaces

---

## 🧠 How It Works

1.  **Database Upload:** The user uploads a SQLite file via the Streamlit sidebar.
2.  **Schema Inspection:** A Python function uses `sqlite3` to query the `sqlite_master` table and `PRAGMA table_info()` to extract all table and column names.
3.  **Prompt Generation:** The user's question and the extracted schema are formatted into a detailed prompt for the Gemini model. This prompt instructs the AI to act as a SQL expert and provides the schema as context.
4.  **AI Query Generation:** The prompt is sent to the Gemini API, which returns a single, clean SQL query string.
5.  **Query Execution:** The app executes this SQL query against the uploaded database using `pandas.read_sql_query`.
6.  **Display Results:** The resulting DataFrame (or any SQL error) is displayed in the Streamlit chat interface.

---

## 💻 Local Installation

To run this project on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/[YOUR_REPO_NAME].git
    cd [YOUR_REPO_NAME]
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    # Create a virtual environment
    python -m venv venv
    
    # Activate it
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    
    # Install required packages
    pip install -r requirements.txt
    ```

3.  **Set up your Environment Variables:**
    Create a file named `.env` in the root directory and add your Google API key:
    ```.env
    GOOGLE_API_KEY="AIza..."
    ```

4.  **Run the Streamlit app:**
    ```bash
    streamlit run src/streamlit_app.py
    ```

---

## 🚀 Deployment to Hugging Face

This app is optimized for deployment on Hugging Face Spaces.

### File Structure

For Hugging Face to correctly identify your app (especially with the `src` layout), your repository must be structured as follows:

## 📁 Project Structure

```bash

Text-to-SQL-Gemini2.5Pro/
├── src/ 
│   ├── .streamlit/ 
│   │     └── config.toml 
│   └── streamlit_app.py
├── .gitignore 
├── requirements.txt 
└── README.md     
```

### Hugging Face Secrets

Do **NOT** upload your `.env` file. Instead, add your API key to the Space's "Repository secrets":

1.  In your Hugging Face Space, go to **Settings**.
2.  Scroll down to **Repository secrets**.
3.  Click **New secret**.
4.  **Name:** `GOOGLE_API_KEY`
5.  **Secret value:** `AIza...`
6.  Click **Save secret**.

### Troubleshooting: 403 Error Fix

Hugging Face Spaces runs Streamlit behind a proxy, which breaks the file uploader and causes a `403 (Forbidden)` error.

**The Fix** is to create a `config.toml` file that disables the XSRF (Cross-Site Request Forgery) protection.

**File Path:** `src/.streamlit/config.toml`

**File Content:**
```toml
[server]
headless = true
enableXsrfProtection = false
enableCORS = true
```
