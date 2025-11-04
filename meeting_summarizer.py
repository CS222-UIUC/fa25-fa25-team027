'''
Meeting Summarizer using Ollama with gpt-oss-120b
This module handles the LLM-based summarization of meeting transcripts using local Ollama models
'''

import json
import ollama
from typing import Dict, Optional


class MeetingSummarizer:
    """
    Handles meeting transcript summarization using local Ollama with gpt-oss-120b
    """

    def __init__(self, model_name: str = "gpt-oss-120b"):
        """
        Initialize the summarizer with a specific Ollama model

        Args:
            model_name: Name of the Ollama model to use (default: gpt-oss-120b)
        """
        self.model_name = model_name
        self._verify_model()

    def _verify_model(self):
        """Verify that the specified model is available in Ollama"""
        try:
            models = ollama.list()
            available_models = [m['name'] for m in models.get('models', [])]
            if not any(self.model_name in m for m in available_models):
                raise ValueError(
                    f"Model '{self.model_name}' not found in Ollama. "
                    f"Available models: {available_models}\n"
                    f"Pull with: ollama pull {self.model_name}"
                )
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to Ollama. Is it running? Error: {e}"
            )

    def _get_system_prompt(self) -> str:
        """
        Returns the system prompt for meeting summarization
        This prompt is carefully designed to get consistent JSON output

        NOTE: Key distinction between output fields:
        - "key_points": Discussion topics (what was talked about)
        - "decisions": Concrete conclusions (what was agreed upon)
        Example: Discussing OAuth vs JWT is a key_point; choosing OAuth is a decision
        """
        return """You are an expert meeting summarizer. Your job is to analyze meeting transcripts and extract structured information.

You must return ONLY valid JSON with this exact structure (no additional text):

{
  "summary_heading": "A brief title for the meeting (max 50 characters)",
  "key_points": [
    "Important discussion point 1",
    "Important discussion point 2",
    ...
  ],
  "action_items": [
    {
      "assignee": "Person's name or 'Unassigned'",
      "task": "Clear description of the task",
      "deadline": "Deadline mentioned or null"
    },
    ...
  ],
  "decisions": [
    "Key decision 1",
    "Key decision 2",
    ...
  ]
}

Guidelines:
- KEY POINTS vs DECISIONS:
  * "key_points": What was DISCUSSED - the main topics and themes talked about
    Example: "Team discussed authentication options (OAuth vs JWT)"
  * "decisions": What was DECIDED - concrete conclusions and commitments made
    Example: "Team decided to implement OAuth for authentication"
  * A meeting may discuss many topics but only reach decisions on some
- Extract 3-7 key points that capture main discussion topics
- Identify all action items with clear owners
- Note any explicit decisions made during the meeting
- If no items exist for a category, use an empty array []
- Keep descriptions concise but informative
- Return ONLY the JSON object, no markdown, no explanation"""

    def summarize(
        self,
        transcript: str,
        max_retries: int = 2
    ) -> Dict:
        """
        Summarize a meeting transcript into structured data

        Args:
            transcript: The full meeting transcript text
            max_retries: Number of times to retry if JSON parsing fails

        Returns:
            Dictionary containing summary_heading, key_points, action_items, decisions

        Raises:
            ValueError: If transcript is empty
            RuntimeError: If unable to get valid JSON after retries
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        result_text = ""  # Initialize to avoid unbound variable errors
        for attempt in range(max_retries + 1):
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {
                            'role': 'system',
                            'content': self._get_system_prompt()
                        },
                        {
                            'role': 'user',
                            'content': f'Summarize this meeting transcript:\n\n{transcript}'
                        }
                    ]
                )

                result_text = response['message']['content'].strip()

                # Try to extract JSON if it's wrapped in markdown code blocks
                if result_text.startswith('```'):
                    # Remove markdown code blocks
                    lines = result_text.split('\n')
                    result_text = '\n'.join(
                        line for line in lines
                        if not line.strip().startswith('```')
                    )

                # Parse JSON
                summary = json.loads(result_text)

                # Validate structure
                required_keys = ['summary_heading', 'key_points', 'action_items', 'decisions']
                if not all(key in summary for key in required_keys):
                    raise ValueError(f"Missing required keys. Got: {summary.keys()}")

                return summary

            except json.JSONDecodeError as e:
                if attempt < max_retries:
                    print(f"JSON parse error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    print(f"Response was: {result_text[:200]}...")
                    continue
                else:
                    raise RuntimeError(
                        f"Failed to get valid JSON after {max_retries + 1} attempts. "
                        f"Last response: {result_text}"
                    )

            except Exception as e:
                raise RuntimeError(f"Summarization failed: {e}")

        # This line should never be reached, but satisfies type checker
        raise RuntimeError("Summarization failed: exceeded maximum retries")

    def summarize_with_fallback(self, transcript: str) -> Dict:
        """
        Summarize with graceful fallback if LLM fails

        Returns a basic structure even if summarization fails
        """
        try:
            return self.summarize(transcript)
        except Exception as e:
            print(f"Warning: Summarization failed: {e}")
            # Return a basic structure
            return {
                "summary_heading": "Meeting Summary (Auto-generated)",
                "key_points": ["Full transcript available below"],
                "action_items": [],
                "decisions": [],
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    # Sample meeting transcript
    sample_transcript = """
    John: Good morning everyone. Let's start our sprint planning meeting.

    Sarah: Thanks John. I think we should focus on the user authentication feature this sprint.

    Mike: I agree with Sarah. The authentication is blocking other features.

    John: Okay, sounds good. Mike, can you take the lead on implementing OAuth integration?

    Mike: Sure, I can do that. I'll aim to have it done by next Wednesday.

    Sarah: I'll work on the UI components for the login page. Should be ready by Thursday.

    John: Perfect. One more thing - we decided last meeting to migrate to PostgreSQL. Are we still on track?

    Mike: Yes, I'll handle that migration this week as well.

    John: Great. So to summarize: Mike handles OAuth and database migration, Sarah handles login UI. Let's meet Friday to review progress.

    Sarah: Sounds good.

    Mike: Agreed. See you all Friday.
    """

    print("=== Meeting Summarizer Test ===\n")

    try:
        # Initialize with default model (gpt-oss-120b)
        summarizer = MeetingSummarizer()
        print(f"✓ Summarizer initialized with model: {summarizer.model_name}\n")

        print("Processing transcript...")
        summary = summarizer.summarize(sample_transcript)

        print("\n--- SUMMARY ---")
        print(json.dumps(summary, indent=2))

        print("\n✓ Summarization successful!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("1. Ollama is installed and running")
        print("2. Model is pulled: ollama pull gpt-oss-120b")
        print("3. Python ollama library is installed: pip install ollama")