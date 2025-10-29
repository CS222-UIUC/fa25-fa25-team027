'''
Test script for Ollama integration
This script tests basic Ollama functionality before integrating with Meeting Minion
'''

try:
    import ollama
    print("✓ Ollama Python library is installed")
except ImportError:
    print("✗ Ollama Python library not found")
    print("  Install it with: pip install ollama")
    exit(1)


def test_basic_connection():
    """Test if Ollama server is running and accessible"""
    print("\n--- Testing Ollama Connection ---")
    try:
        # Try to list available models
        models = ollama.list()
        print("✓ Successfully connected to Ollama")
        print(f"  Available models: {len(models.get('models', []))}")
        for model in models.get('models', []):
            print(f"    - {model['name']}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Ollama: {e}")
        print("  Make sure Ollama is running")
        return False


def test_simple_chat():
    """Test basic chat functionality"""
    print("\n--- Testing Simple Chat ---")
    try:
        response = ollama.chat(
            model='llama3.2:1b',  # You can change this to any model you have
            messages=[
                {
                    'role': 'user',
                    'content': 'Say "Hello from Ollama!" and nothing else.'
                }
            ]
        )
        print("✓ Chat successful")
        print(f"  Response: {response['message']['content']}")
        return True
    except Exception as e:
        print(f"✗ Chat failed: {e}")
        if "model" in str(e).lower():
            print("  The model might not be downloaded yet.")
            print("  Download it with: ollama pull llama3.2")
        return False


def test_structured_output():
    """Test getting JSON-structured output (for meeting summaries)"""
    print("\n--- Testing Structured JSON Output ---")

    # Sample meeting transcript
    sample_transcript = """
    John: Hey everyone, thanks for joining. Today we need to discuss the Q4 roadmap.
    Sarah: I think we should prioritize the mobile app redesign.
    John: Good point. Mike, can you lead that effort?
    Mike: Sure, I'll start next week. I'll need 2 designers assigned to my team.
    Sarah: I'll also work on updating our documentation by end of month.
    John: Perfect. Let's meet again next Friday to check progress.
    """

    try:
        response = ollama.chat(
            model='llama3.2:1b',
            messages=[
                {
                    'role': 'system',
                    'content': '''You are a meeting summarizer. Extract information and return ONLY valid JSON with this exact structure:
{
  "key_points": ["point 1", "point 2", ...],
  "action_items": [
    {"assignee": "person name", "task": "task description", "deadline": "deadline or null"},
    ...
  ],
  "decisions": ["decision 1", "decision 2", ...]
}
Do not include any text outside the JSON.'''
                },
                {
                    'role': 'user',
                    'content': f'Summarize this meeting:\n{sample_transcript}'
                }
            ]
        )

        result = response['message']['content']
        print("✓ Got response from model")
        print(f"\nRaw response:\n{result}")

        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(result)
            print("\n✓ Response is valid JSON")
            print(f"  Key points: {len(parsed.get('key_points', []))}")
            print(f"  Action items: {len(parsed.get('action_items', []))}")
            print(f"  Decisions: {len(parsed.get('decisions', []))}")
            return True
        except json.JSONDecodeError as je:
            print(f"\n✗ Response is not valid JSON: {je}")
            print("  You may need to improve the prompt or try a different model")
            return False

    except Exception as e:
        print(f"✗ Structured output test failed: {e}")
        return False


if __name__ == "__main__":
    print("=== Ollama Integration Test Suite ===")

    # Run tests
    tests_passed = 0
    tests_total = 3

    if test_basic_connection():
        tests_passed += 1

    if test_simple_chat():
        tests_passed += 1

    if test_structured_output():
        tests_passed += 1

    print(f"\n{'='*40}")
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("✓ All tests passed! Ollama is ready for Meeting Minion")
    else:
        print("⚠ Some tests failed. See messages above for details.")
