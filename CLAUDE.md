# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based SQLite database wrapper library that provides simplified CRUD operations. The main module `db_func.py` contains a complete abstraction layer for database operations using sqlite3.

## Core Architecture

### Database Module (`db_func.py`)

The module provides dictionary-based CRUD operations with the following key characteristics:

- **Case Handling**: All column names are automatically uppercased internally, allowing case-insensitive operations
- **Row Factory**: Uses `sqlite3.Row` for dict-like row access
- **Parameterized Queries**: All user inputs are properly parameterized to prevent SQL injection

### Table Schema Specification Format

Tables are created using a dictionary specification with this structure:

```python
spec = {
    "column_name": ["DATATYPE", "optional_specifiers"],
    "Primary Key": "column_name",  # Optional
    "Foreign Key": [(col_name, ref_table)]  # Optional, list of tuples
}
```

Primary key columns automatically get `NOT NULL UNIQUE PRIMARY KEY` constraints. Refer to https://www.w3schools.com/sql/sql_datatypes.asp for SQLite datatypes.

### Key Functions

- `create_database(name)` / `connect_database(path)`: Database connection management
- `create_table(conn, spec, name)`: Creates tables from dictionary specs
- `single_insert(conn, cmd_dict, name)`: Dictionary-based row insertion
- `select(conn, col_list, where_clause, order_by, name)`: Flexible SELECT queries
  - `where_clause` can be dict (for AND conditions) or raw SQL string
  - `order_by` can be list or string
- `update(conn, col_list, where_clause, name)`: Updates rows, returns affected count
- `delete(conn, cmd_dict, name)`: Deletes rows, returns deleted count
- `drop_table(conn, name)`: Table deletion

## Development Commands

### Running Tests

```bash
python3 test_db.py
```

This test suite creates a temporary `test.db`, runs all CRUD operations, and cleans up by dropping tables (the .db file persists for inspection).

### Testing Individual Functions

Import the module and use Python's interactive mode:

```bash
python3
>>> import db_func as db
>>> conn = db.create_database("test")
>>> # Your test code here
```

## Important Conventions

- All table and column names are case-insensitive (uppercased internally)
- WHERE clauses accept either dictionaries (for simple AND conditions) or raw SQL strings for complex queries
- Always commit after INSERT, UPDATE, or DELETE operations (handled by the functions)
- The module uses parameterized queries throughout for security
- Database files are .db extension and gitignored

## Project Structure

- `db_func.py` - Core database wrapper library (low-level CRUD operations)
- `meeting_db.py` - Meeting-specific database layer (uses db_func.py)
- `app.py` - Streamlit web application (uses meeting_db.py for persistence)
- `meeting_summarizer.py` - LLM-based meeting summarization
- `test_db.py` - Manual test suite for db_func
- `test_db_func.py` - Automated unit tests for db_func (32 tests)
- `test_meeting_db.py` - Integration tests for meeting_db (20 tests)
- `test_meeting_summarizer.py` - Unit tests for summarizer (12 tests)
- `test_e2e_persistence.py` - End-to-end persistence test
- `.gitignore` - Excludes *.db files and __pycache__



## Database Integration

### Meeting Database (`meeting_db.py`)

The `MeetingDatabase` class provides persistent storage for meeting records:

**Schema:**
- `meetings` table: id, created_at, title, transcript, summary_heading
- `key_points` table: meeting_id (FK), point, point_order
- `action_items` table: meeting_id (FK), assignee, task, deadline, item_order
- `decisions` table: meeting_id (FK), decision, decision_order

**Key Features:**
- Automatic schema initialization
- Preserves order of key points, action items, and decisions
- SQL-based pagination (LIMIT/OFFSET)
- Cascade delete support
- Column name normalization (db_func uppercases internally, meeting_db normalizes to lowercase)

**Usage in app.py:**
- Meetings are saved to `meetings.db` when processed
- History panel loads from database with pagination
- Data persists across app restarts (no session state needed)

**Testing:**
- 20 integration tests in `test_meeting_db.py` (100% pass rate)
- End-to-end persistence test in `test_e2e_persistence.py`
- Verifies data integrity across close/reopen cycles

## About the project
AI Usage Disclosure
Tool Used: ChatGPT
Purpose: I used ChatGPT to help brainstorm the initial project idea ("Meeting Minion")
from a list of options. For this draft, I used it as a sanity check to ensure the technical
components (like WhisperX and Streamlit) were appropriate for a moderate skill level
and to brainstorm potential risks and a realistic timeline. I also used it to help adapt the
formal guidelines into the more creative "man in the yellow hat" framing.
Prompt:
"I am taking a CS222, a computer science project course
I joined a group. We are interested in AI & LLM. Can you brainstorm some ideas for the
potential project? Assume our programming skills are moderate”
Project Proposal Draft: "Meeting Minion"
Team Number: 27
Team Members:
●
●
●
●
James Weng [zweng7]
Avaneesh Kumar [ak109]
Himanshu Udupi [hudupi2]
Dhruv Agrawal [dhruva6]
Pitch
Keeping track of meeting notes is a universal challenge, whether you're a researcher in
Antarctica, coordinating a supply run, or a student in a project meeting. Meeting Minion is a
web app that automatically turns meeting recordings into structured summaries, highlighting
key decisions, action items, and discussion points so that you can focus on the conversation
instead of frantic note-taking.
Functionality
1. Users can upload an audio file (e.g., .mp3, .wav) or the transcript from a Zoom meeting.
2. Users can view a real-time progress indicator while the audio is being processed.
3. Users are presented with a complete, written transcript of the meeting.
4. Users are presented with a structured summary that lists the key ideas discussed.
5. Users are presented with a list of potential action items allowing them to distribute the
same.
6. Users can download the transcript and summary as a text file for their records.
7. Users can store their meeting history and summaries without needing to store the
heavier audio files.
8. Supports pagination for the history of summaries in order to partially load results when
browsing to avoid overload on servers.
9. The files for transcription are not stored and would be our responsibility to ensure if
using any third-party APIs, they are not storing any details shared.
Components
Our project deliverables would be an end-to-end full stack AI application that supports
multi-model input from the user through an intuitive interface/frontend and processes the same
by leveraging LLM-based transcription and inference to produce a list of key points and action
items from the meeting while persisting the results in a data store to avoid multiple inference
cost for the same input.
Diving deeper into each component:
1. Frontend
●
●
●
●
●
Functionality: This component is the user interface. Its job is to let the user upload a
file, show a progress bar, and display the final transcript and summary in a clean,
easy-to-read format. We chose to separate this from the backend so that the user-facing
part is simple and responsive, without being bogged down by the heavy processing.
Programming Language: Python. We are using Python for the entire project because
it has excellent support for AI and data processing libraries, and our team has moderate
experience with it. This consistency simplifies development.
Major Libraries Used: Streamlit. This library is perfect for our needs because it lets
us build a clean web app using only Python scripts, without needing to know HTML,
CSS, or JavaScript. It's the fastest way to get from an idea to a working prototype.
Testing Methodology: We will use pytest with Streamlit's testing utilities to write unit
tests for the frontend logic (e.g., testing file upload handling) and component tests to
ensure the UI renders correctly. This is appropriate because it allows us to verify that the
user interface behaves as expected automatically.
Interactions With Other Components: The frontend sends the user's audio file to
the backend via a function call (since Streamlit and our backend logic will run in the
same application). It then waits for the backend to return the transcript and summary
data, which it displays.
2. LLM Transcription and Information Extraction
●
●
●
Functionality: This component does the heavy lifting. It receives the audio file,
converts it to text, and then analyzes the text to create a structured summary. Breaking
this into a separate logical component keeps the code organized and makes it easy to
improve the transcription or summary logic independently.
Programming Language: Python.
Major Libraries Used:
○
○
WhisperX model: We will use the lighter model based on top of the OpenAI
Whisper model for audio transcription. It is more accurate with reference to
real-time transcriptions and word-level timestamps. This saves us the cost of
running inference using the OpenAI closed-source model every time we get a new
audio file.
OpenAI GPT-OSS model: We will use OpenAI’s open source foundational LLM to
generate the summary. In order to test run these models locally, we will be using
●
●
Ollama that allows us to run these models in a lightweight manner. We will
carefully design prompts to ensure the output into a structured JSON format for
easy parsing.
○
Python json and os libraries: For handling data and file operations.
Testing Methodology: We will use pytest to write unit tests for each function in the
backend. For example, we can test the function that parses the LLM's JSON output with
mock data to ensure it correctly extracts action items, even before connecting to the real
API. This strategy isolates our logic from external services, making tests fast and reliable.
Interactions With Other Components: The backend is called by the frontend. It
takes the audio file, calls the WhisperX and GPT-OSS models, processes the results, and
sends the structured data back to the frontend.
3. Data Store
●
●
●
●
●
Functionality: This component helps us improve our performance by allowing the user
to view their past meeting summaries and allows us to maintain extensibility by
maintaining the global action items mapped to their respective meetings. This would
allow us to showcase the action items in a fresh and checklist manner and allow the user
to get more context by accessing the meeting summary.
Programming Language: SQL and Python (driver code)
Major Libraries Used:
○
SQLite: SQLite is a lightweight SQL database that integrates well with Python
keeping the codebase uniform while allowing us to maintain persistence of the
data. We choose to use a relational database over NoSQL since each action item
shares a one-to-one relationship with their respective meeting that can be
represented and queried easily.
Testing Methodology: We can avoid any overhead to test this code since we don’t
need any new libraries to test. The database driver code in Python can be tested using
pytest and sending the requests to the database through a Data Access Object (DAO)
layer. We will directly test the database by sending queries, however, in a production
setting, it would be beneficial to mock the DB using unittest.mock.
Interactions With Other Components: The DAO will have the functions to interact
with the SQLite DB and returns the results to the frontend to display the previous
meetings and action items of the user in a paginated list. We can abstract this layer if we
need to manipulate the results and implement a pagination token on the server-side
before sending it to the client-side frontend.
User Flow Diagram (Component Interaction Diagram):
Continuous Integration
●
●
●
●
Testing Library: We will use pytest for running our unit and component tests.
Style Guide: We will follow the PEP 8 style guide for Python code. We will use the black
code formatter and flake8 linter to check and enforce this style automatically.
Test Coverage: We will use the pytest-cov library to compute test coverage, which
generates a report showing what percentage of our code is executed by our tests.
Pull Request (PR) Workflow:
○
When to open PRs: A PR will be opened for any new feature or bug fix. No one
will push directly to the main branch.
○
Selecting Reviewers: The team member creating the PR will assign one other
random team member as a reviewer.
○
Avoiding Merge Conflicts: To avoid conflicts, team members will create a new
branch from the latest main for each feature they work on. They will frequently
pull changes from main into their feature branch to stay up-to-date.
Schedule
Week Tasks
Week 1
1. Set up project repository, CI/CD pipeline,
and Streamlit.
2. Create a basic frontend with a file upload
button.
Week 2
1. Implement backend function to process
audio using WhisperX.
2. Display the raw transcript on the frontend.
Week 3
1. Design and test prompts for the LLM to
generate summaries.
2. Implement backend function to call the
LLM API.
Week 4
1. Create a function to parse the LLM's JSON
response.
2. Display the unstructured summary on the
frontend.
Week 5
1. Improve the prompt to reliably extract
action items.
2. Update the frontend to display actions in a
dedicated list.
Week 6
1. Improve the prompt to reliably extract key
decisions.
2. Update the frontend to display decisions in
a dedicated list.
Week 7
1. Add a progress bar to the frontend for
better UX.
2. Implement the download feature for
transcripts/summaries.
Week 8
1. Write comprehensive unit tests for backend
functions.
2. Polish the frontend layout and styling for
clarity.
Week 9
1. Conduct end-to-end testing and fix bugs.
2. Work on stretch goals (e.g., speaker
diarization).
Week 10
1. Final code cleanup, documentation, and
preparation for the demo.
2. Buffer time for any unforeseen delays.
Risks
1. Risk: Since we are running the models for transcription and extraction locally, we
would need to handle surges and throttle malicious requests.
○
Resolution Plan: We will monitor usage closely from the start. We will implement
the data store so we don't re-process the same file accidentally. Using these
trends, we can establish quotas to implement throttling requests if there is a
surge of requests.
○
Schedule Impact: 2-3 days to implement metrics and visualise the results
○
Adjustment: This work would be done in Week 7 or 8 when all the features are
finalised.
2. Risk: The LLM might not consistently return well-formatted JSON, breaking our
application.
○
Resolution Plan: We will invest significant time in "prompt engineering" early on.
Our parsing function will also be designed to handle errors gracefully and log any
inadequate responses, allowing us to improve the prompt.
○
Schedule Impact: Up to 1 week of iterative testing and prompt refinement.
○
Adjustment: We would use the buffer time in Week 10, ensuring core
functionality (transcription) is always working.
3. Risk: Processing long meetings (e.g., 60+ minutes) might cause timeouts in our app or
the APIs.
○
○
○
Resolution Plan: We will initially impose a reasonable file length limit (e.g., 15
minutes). For a future version, we could split long audio into chunks, but for our
Minimum Viable Product (MVP), a time limit is acceptable.
Schedule Impact: Minimal (1 day to implement the limit).
Adjustment: This would be tackled in Week 2 as part of the upload function, with
no significant schedule impact.
Teamwork
To reduce friction, we will use a Docker container to standardize our development environment.
This ensures that everyone has identical versions of Python and libraries, preventing the classic
problem of code that works on one monkey's computer but not another's. This is especially
important for a data-focused project with many dependencies.
We will divide work based on a frontend/backend split, which aligns with our initial interests.
Two team members will focus primarily on the frontend and user experience, while the other
two will focus on the backend processing, API integration, and prompt engineering. We will use
an Asana board to manage tasks, and team members will select new tasks from the "To Do"
column once they have finished their current one, ensuring a fair and flexible division of labor.