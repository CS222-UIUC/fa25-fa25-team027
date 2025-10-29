# Ollama Setup Guide for Meeting Minion

This guide will help you set up Ollama for local LLM inference in the Meeting Minion project.

## Step 1: Install Ollama

### macOS
```bash
# Download and install from the official website
# Visit: https://ollama.com/download
# Or use Homebrew:
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Download the installer from https://ollama.com/download

## Step 2: Start Ollama Server

Ollama runs as a background service, but you can start it manually:

```bash
ollama serve
```

Usually it starts automatically after installation on macOS/Windows.

## Step 3: Download a Model

For Meeting Minion, we recommend starting with `llama3.2` (smaller, faster) or `llama3.1` (more capable):

```bash
# For a lighter model (good for testing, ~2GB)
ollama pull llama3.2

# OR for better quality (larger, ~4.7GB)
ollama pull llama3.1

# OR for the smallest model (very fast, ~1GB)
ollama pull llama3.2:1b
```

You can see all available models at: https://ollama.com/library

## Step 4: Install Python Library

```bash
pip install ollama
```

## Step 5: Test Your Setup

Run the test script:

```bash
python3 test_ollama.py
```

This will verify:
- Ollama is installed and running
- You can communicate with the model
- JSON-structured output works (critical for Meeting Minion)

## Troubleshooting

### "Failed to connect to Ollama"
- Make sure Ollama is running: `ollama serve`
- Check if it's running: `curl http://localhost:11434`

### "Model not found"
- Download the model first: `ollama pull llama3.2`
- List available models: `ollama list`

### Response is not valid JSON
- Some models are better at structured output than others
- Try adding more specific instructions in the prompt
- Consider using `llama3.1` or `mistral` for better JSON adherence

## Recommended Models for Meeting Minion

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3.2:1b | ~1GB | Very Fast | Good | Development/Testing |
| llama3.2 | ~2GB | Fast | Very Good | Production (small meetings) |
| llama3.1 | ~4.7GB | Medium | Excellent | Production (better summaries) |
| mistral | ~4GB | Medium | Excellent | Production (good at JSON) |

## Next Steps

Once setup is complete:
1. Run `test_ollama.py` to verify everything works
2. Review the structured output format in the test
3. Integrate with WhisperX transcripts
4. Fine-tune prompts for your specific meeting format
