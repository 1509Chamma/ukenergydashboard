**Project Deployment:** [https://ukenergydashboard.streamlit.app](https://ukenergydashboard.streamlit.app) <br>
**Project Documentation:** documentation/project_documentation.md <br>
**Assignment Brief:** documentation/assignment_brief.md <br>

## Overview

An interactive Streamlit dashboard analysing UK electricity demand, generation, carbon intensity, and weather data.
The dashboard focuses on clear visualisation and simple interactive exploration of energy trends.

---

## Run Locally

### Requirements

* Python 3.10+(3.13.9 recommended)
* pip
* virtual environment

### 1. Clone the repository

```bash
git clone https://github.com/1509Chamma/ukenergydashboard.git
cd ukenergydashboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate     # macOS / Linux
.\.venv\Scripts\Activate.ps1  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment variables and database setup

This project uses **Supabase** as a backend database.

To run the dashboard locally, you must:

1. **Create a Supabase project**

   * Go to [https://supabase.com](https://supabase.com)
   * Create a new project
   * Copy the **Project URL** and **Anon Key**

2. **Create the required database schema**

   * The required tables and schema definitions are provided in the **project documentation**
   * Create these tables in the Supabase SQL editor before running the app

3. **Populate the database with historic data**

   * Open and run the `data_analysis` notebook included in this repository
   * The notebook uploads historic data to your Supabase database
   * Ensure your Supabase credentials are set before running the notebook

4. **Create a `.env` file in the project root**

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Do **not** commit this file to version control.

Once the database is populated, the Streamlit application can be run locally.



### 5. Run the app

```bash
streamlit run src/app.py
```

Open: [http://localhost:8501](http://localhost:8501)



