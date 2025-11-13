[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/19BwrNgF)

# Meeting Minion

**Turn meeting recordings into structured summaries, action items, and transcripts automatically.**

Meeting Minion is a web application that uses AI to process meeting recordings and generate structured summaries with key points, decisions, and action items. Built with Streamlit, WhisperX, and local LLM inference via Ollama.

---

## Features

- **Audio Transcription**: Upload audio files (.mp3, .wav, .m4a) for automatic transcription using WhisperX
- **Speaker Diarization**: Identify and label different speakers in the meeting
- **AI Summarization**: Generate structured summaries using local LLM (gpt-oss-120b via Ollama)
- **Structured Output**:
  - Summary heading
  - Key discussion points
  - Decisions made
  - Action items with assignees and deadlines
- **Meeting History**: Store and browse past meetings with pagination
- **Download Options**: Export transcripts and summaries as text files
- **Privacy-Focused**: All processing happens locally - no data sent to external APIs

---

## Quick Start

### Prerequisites

- Python 3.10 or 3.11
- [Ollama](https://ollama.ai/download) installed and running
- FFmpeg (for audio processing)

### Installation

#### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd fa25-fa25-team027
```

#### Step 2: Install Dependencies

**Option A: Simple installation (recommended)**

```bash
# Install core packages without version conflicts
pip3 install streamlit whisperx ollama pytest pytest-cov
```

**Option B: Use requirements file**

```bash
# Install all dependencies
pip3 install -r requirements-clean.txt

# For development (includes testing tools)
pip3 install -r requirements-dev.txt
```

**Option C: Use virtual environment (recommended for isolation)**

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt
```

#### Step 3: Install Ollama and Model

```bash
# Install Ollama from https://ollama.ai/download

# Pull the required model
ollama pull gpt-oss-120b

# Verify installation
ollama list
```

#### Step 4: Verify Installation

```bash
# Test that all packages are installed
python3 -c "import streamlit, whisperx, ollama, pytest; print('✅ All packages installed!')"
```

---

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Using the Application

**Option 1: Upload Audio File**

1. Click "Browse files" in the sidebar
2. Upload an audio file (.mp3, .wav, .m4a)
3. Set the number of speakers (1-5)
4. Enter speaker names
5. Wait for transcription to appear
6. Optionally edit the transcript
7. Click "Process" to generate summary

**Option 2: Paste Transcript**

1. Scroll to "OR paste a transcript" in the sidebar
2. Paste your meeting transcript
3. Enter a meeting title
4. Click "Process" to generate summary

### Viewing Results

After processing, you'll see:
- **Transcript**: Full meeting transcript with speaker labels
- **Summary**: Key discussion points and decisions
- **Action Items**: Tasks with assignees and deadlines
- **Download Options**: Export transcript and summary as text files

### Meeting History

- View past meetings in the History section
- Browse with pagination
- Download previous transcripts and summaries

---

## Testing

### Running Unit Tests

The project includes comprehensive unit tests for all business logic:

```bash
# Run all tests
pytest test_meeting_summarizer.py test_db_func.py -v

# Run with coverage report
pytest test_meeting_summarizer.py test_db_func.py --cov=. --cov-report=term-missing

# Run specific test file
pytest test_db_func.py -v

# Run specific test
pytest test_db_func.py::TestDatabaseCreation::test_create_database -v
```

**Expected Results:**
- 44 tests should pass
- Coverage: ~99% for business logic (db_func.py, meeting_summarizer.py)

### Test Coverage

- **db_func.py**: 99.23% coverage (32 tests)
- **meeting_summarizer.py**: 98% coverage (12 tests)
- **app.py**: 0% coverage (tested manually - this is expected for UI layers)

### Manual Testing

Test the full application manually:

1. **Test with Sample Transcript:**
   ```
   John: Good morning team. Let's discuss the new feature.
   Sarah: I can handle the frontend work.
   Mike: I'll take care of the backend API.
   John: Great. Sarah, can you finish by Friday?
   Sarah: Yes, Friday works.
   John: Perfect. We've decided to use React for this feature.
   ```

2. **Verify Output:**
   - Key points identified correctly
   - Action items extracted (Sarah - frontend, due Friday)
   - Decisions captured (Using React)
   - Meeting saved in History

### Testing Checklist

- [ ] Unit tests pass (44/44)
- [ ] App starts without errors
- [ ] Can upload audio file
- [ ] Transcription works
- [ ] Can paste transcript
- [ ] Summary generated correctly
- [ ] Action items formatted properly
- [ ] Download buttons work
- [ ] History displays past meetings
- [ ] Error handling works (no Ollama)

---

## Project Structure

```
fa25-fa25-team027/
├── app.py                      # Main Streamlit application
├── meeting_summarizer.py       # LLM-based summarization module
├── db_func.py                  # SQLite database wrapper
├── test_meeting_summarizer.py # Unit tests for summarizer
├── test_db_func.py             # Unit tests for database
├── test_db.py                  # Manual test script
├── requirements-clean.txt      # Core dependencies
├── requirements-dev.txt        # Development dependencies
├── pytest.ini                  # Pytest configuration
├── .coveragerc                 # Coverage configuration
├── .flake8                     # Linting configuration
├── pyproject.toml              # Black formatter configuration
├── .github/workflows/ci.yml    # CI/CD pipeline
├── INSTALL.md                  # Detailed installation guide
├── TESTING.md                  # Comprehensive testing guide
├── REQUIREMENTS_GUIDE.md       # Requirements files explanation
└── README.md                   # This file
```

---

## Development

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd fa25-fa25-team027

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Verify setup
pytest test_meeting_summarizer.py test_db_func.py -v
```

### Development Workflow

1. **Make changes** to code
2. **Quick manual test** (optional):
   ```bash
   python3 test_db.py
   # OR
   streamlit run app.py
   ```
3. **Run tests**:
   ```bash
   pytest test_meeting_summarizer.py test_db_func.py -v
   ```
4. **Check code quality**:
   ```bash
   black --check .
   flake8 . --exclude=venv
   ```
5. **Commit changes**

### Code Quality Tools

**Formatting with Black:**
```bash
# Check formatting
black --check .

# Auto-format code
black .
```

**Linting with Flake8:**
```bash
flake8 . --exclude=venv
```

**Security Scanning:**
```bash
bandit -r . -x ./venv,./test_*.py
```

---

## CI/CD Pipeline

The project includes a GitHub Actions workflow that automatically:

- Runs on push/pull request to `main` or `develop` branches
- Tests on Python 3.10 and 3.11
- Runs all unit tests
- Generates coverage reports
- Uploads to Codecov
- Runs linting and formatting checks
- Performs security scans

**Configuration:** `.github/workflows/ci.yml`

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'pytest'"
```bash
pip3 install pytest pytest-cov pytest-mock
```

### "Model 'gpt-oss-120b' not found"
```bash
ollama pull gpt-oss-120b
```

### "Cannot connect to Ollama"
```bash
# Check if Ollama is running
ollama list

# Start Ollama (it should run as a service)
# On macOS: Check if Ollama app is running
# On Linux: systemctl start ollama
```

### "Failed to initialize MeetingSummarizer"
- Ensure Ollama is running
- Verify model is installed: `ollama list`
- Pull the model: `ollama pull gpt-oss-120b`

### Streamlit won't start
```bash
pip3 install streamlit
streamlit run app.py
```

### Version conflicts during installation
```bash
# Use the minimal requirements file
pip3 install -r requirements-clean.txt

# Or install packages individually
pip3 install streamlit whisperx ollama pytest pytest-cov
```

---

## Team Members

- James Weng [zweng7]
- Avaneesh Kumar [ak109]
- Himanshu Udupi [hudupi2]
- Dhruv Agrawal [dhruva6]

---

## Architecture

### Components

1. **Frontend (app.py)**
   - Streamlit web interface
   - File upload handling
   - Results display
   - History management

2. **Audio Processing (WhisperX)**
   - Audio transcription
   - Speaker diarization
   - Word-level timestamps

3. **Summarization (meeting_summarizer.py)**
   - LLM-based analysis using Ollama
   - Structured JSON output
   - Error handling and fallbacks

4. **Data Storage (db_func.py)**
   - SQLite database wrapper
   - CRUD operations
   - Meeting history persistence

### Data Flow

```
Audio File → WhisperX → Transcript → Ollama LLM → Structured Summary
                ↓                            ↓
        Display in UI                Save to Database
```

---

## Testing Strategy

- **Unit Tests**: Business logic (db_func.py, meeting_summarizer.py)
  - Coverage: 99%
  - Automated with pytest
  - Run in CI/CD

- **Manual Tests**: UI layer (app.py)
  - Tested via Streamlit interface
  - Manual checklist verification

- **Integration Tests**: End-to-end workflow
  - Manual testing with real audio files
  - Verify complete pipeline

---

## Dependencies

### Core Dependencies

- **streamlit**: Web application framework
- **whisperx**: Audio transcription with speaker diarization
- **ollama**: Local LLM inference
- **torch/torchaudio**: PyTorch for ML models
- **sqlite3**: Database (built into Python)

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **black**: Code formatting
- **flake8**: Linting
- **bandit**: Security scanning

See `requirements-clean.txt` for the complete list.

---

## Additional Documentation

- **[INSTALL.md](INSTALL.md)**: Detailed installation instructions and troubleshooting
- **[TESTING.md](TESTING.md)**: Comprehensive testing guide with examples
- **[REQUIREMENTS_GUIDE.md](REQUIREMENTS_GUIDE.md)**: Explanation of requirements files
- **[STREAMLIT_TESTING.md](STREAMLIT_TESTING.md)**: Guide to testing Streamlit applications
- **[TEST_COMPARISON.md](TEST_COMPARISON.md)**: Comparison of test files
- **[CLAUDE.md](CLAUDE.md)**: Project context for Claude Code

---

## License

[Add your license information here]

---

## Acknowledgments

- OpenAI Whisper for speech recognition technology
- WhisperX for enhanced transcription capabilities
- Ollama for local LLM inference
- Streamlit for the web framework
