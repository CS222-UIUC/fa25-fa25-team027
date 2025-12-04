"""
Unit tests for meeting_summarizer.py
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from ..meeting_summarizer import MeetingSummarizer


class TestMeetingSummarizer:
    """Test suite for MeetingSummarizer class"""

    @patch("meeting_summarizer.ollama.list")
    def test_init_success(self, mock_list):
        """Test successful initialization when model is available"""
        # Mock the ollama.list() response
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        summarizer = MeetingSummarizer()
        assert summarizer.model_name == "gpt-oss-120b"

    @patch("meeting_summarizer.ollama.list")
    def test_init_model_not_found(self, mock_list):
        """Test initialization fails when model is not available"""
        # Mock empty model list
        mock_list.return_value = MagicMock(models=[])

        with pytest.raises(ValueError) as exc_info:
            MeetingSummarizer()

        assert "Model 'gpt-oss-120b' not found" in str(exc_info.value)

    @patch("meeting_summarizer.ollama.list")
    def test_init_ollama_not_running(self, mock_list):
        """Test initialization fails when Ollama is not running"""
        # Mock connection error
        mock_list.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError) as exc_info:
            MeetingSummarizer()

        assert "Cannot connect to Ollama" in str(exc_info.value)

    @patch("meeting_summarizer.ollama.list")
    @patch("meeting_summarizer.ollama.chat")
    def test_summarize_success(self, mock_chat, mock_list):
        """Test successful summarization with valid JSON response"""
        # Setup mocks
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        valid_response = {
            "summary_heading": "Sprint Planning Meeting",
            "key_points": ["Discussed authentication feature", "Reviewed database migration plan"],
            "action_items": [
                {
                    "assignee": "Mike",
                    "task": "Implement OAuth integration",
                    "deadline": "Next Wednesday",
                }
            ],
            "decisions": ["Team will use PostgreSQL"],
        }

        mock_chat.return_value = {"message": {"content": json.dumps(valid_response)}}

        summarizer = MeetingSummarizer()
        transcript = "John: Let's discuss authentication. Mike: I'll handle OAuth."

        result = summarizer.summarize(transcript)

        assert result["summary_heading"] == "Sprint Planning Meeting"
        assert len(result["key_points"]) == 2
        assert len(result["action_items"]) == 1
        assert result["action_items"][0]["assignee"] == "Mike"
        assert len(result["decisions"]) == 1

    @patch("meeting_summarizer.ollama.list")
    @patch("meeting_summarizer.ollama.chat")
    def test_summarize_with_markdown_wrapper(self, mock_chat, mock_list):
        """Test summarization handles JSON wrapped in markdown code blocks"""
        # Setup mocks
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        valid_response = {
            "summary_heading": "Test Meeting",
            "key_points": ["Point 1"],
            "action_items": [],
            "decisions": [],
        }

        # Wrap JSON in markdown code blocks (common LLM behavior)
        markdown_wrapped = f"```json\n{json.dumps(valid_response)}\n```"

        mock_chat.return_value = {"message": {"content": markdown_wrapped}}

        summarizer = MeetingSummarizer()
        result = summarizer.summarize("Test transcript")

        assert result["summary_heading"] == "Test Meeting"
        assert len(result["key_points"]) == 1

    @patch("meeting_summarizer.ollama.list")
    def test_summarize_empty_transcript(self, mock_list):
        """Test that empty transcript raises ValueError"""
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        summarizer = MeetingSummarizer()

        with pytest.raises(ValueError) as exc_info:
            summarizer.summarize("")

        assert "Transcript cannot be empty" in str(exc_info.value)

    @patch("meeting_summarizer.ollama.list")
    @patch("meeting_summarizer.ollama.chat")
    def test_summarize_invalid_json(self, mock_chat, mock_list):
        """Test that invalid JSON triggers retry and eventually fails"""
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        # Return invalid JSON on all attempts
        mock_chat.return_value = {"message": {"content": "This is not valid JSON"}}

        summarizer = MeetingSummarizer()

        with pytest.raises(RuntimeError) as exc_info:
            summarizer.summarize("Test transcript", max_retries=1)

        assert "Failed to get valid JSON" in str(exc_info.value)

    @patch("meeting_summarizer.ollama.list")
    @patch("meeting_summarizer.ollama.chat")
    def test_summarize_missing_keys(self, mock_chat, mock_list):
        """Test that response with missing required keys fails"""
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        # Missing 'decisions' key
        incomplete_response = {"summary_heading": "Test", "key_points": [], "action_items": []}

        mock_chat.return_value = {"message": {"content": json.dumps(incomplete_response)}}

        summarizer = MeetingSummarizer()

        with pytest.raises(RuntimeError) as exc_info:
            summarizer.summarize("Test transcript", max_retries=0)

        assert "Missing required keys" in str(exc_info.value)

    @patch("meeting_summarizer.ollama.list")
    @patch("meeting_summarizer.ollama.chat")
    def test_summarize_with_fallback_success(self, mock_chat, mock_list):
        """Test summarize_with_fallback returns valid result on success"""
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        valid_response = {
            "summary_heading": "Test Meeting",
            "key_points": ["Point 1"],
            "action_items": [],
            "decisions": [],
        }

        mock_chat.return_value = {"message": {"content": json.dumps(valid_response)}}

        summarizer = MeetingSummarizer()
        result = summarizer.summarize_with_fallback("Test transcript")

        assert result["summary_heading"] == "Test Meeting"
        assert "error" not in result

    @patch("meeting_summarizer.ollama.list")
    @patch("meeting_summarizer.ollama.chat")
    def test_summarize_with_fallback_error(self, mock_chat, mock_list):
        """Test summarize_with_fallback returns fallback structure on error"""
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        # Simulate error
        mock_chat.side_effect = Exception("API Error")

        summarizer = MeetingSummarizer()
        result = summarizer.summarize_with_fallback("Test transcript")

        # Should return fallback structure
        assert result["summary_heading"] == "Meeting Summary (Auto-generated)"
        assert result["key_points"] == ["Full transcript available below"]
        assert result["action_items"] == []
        assert result["decisions"] == []
        assert "error" in result

    @patch("meeting_summarizer.ollama.list")
    def test_custom_model_name(self, mock_list):
        """Test initialization with custom model name"""
        mock_model = MagicMock()
        mock_model.model = "custom-model"
        mock_list.return_value = MagicMock(models=[mock_model])

        summarizer = MeetingSummarizer(model_name="custom-model")
        assert summarizer.model_name == "custom-model"

    @patch("meeting_summarizer.ollama.list")
    def test_system_prompt_structure(self, mock_list):
        """Test that system prompt contains required elements"""
        mock_model = MagicMock()
        mock_model.model = "gpt-oss-120b"
        mock_list.return_value = MagicMock(models=[mock_model])

        summarizer = MeetingSummarizer()
        prompt = summarizer._get_system_prompt()

        # Check for key elements in the system prompt
        assert "summary_heading" in prompt
        assert "key_points" in prompt
        assert "action_items" in prompt
        assert "decisions" in prompt
        assert "JSON" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
