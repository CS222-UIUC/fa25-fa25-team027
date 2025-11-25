'''
Integration tests for meeting_db module
Tests the MeetingDatabase class and its interaction with db_func
'''

import pytest
import os
from meeting_db import MeetingDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    db_path = "test_meeting_integration.db"
    # Remove if exists
    if os.path.exists(db_path):
        os.remove(db_path)

    db = MeetingDatabase(db_path)
    yield db

    # Cleanup
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestMeetingDatabaseInit:
    """Test database initialization"""

    def test_database_creation(self, temp_db):
        """Test that database and tables are created"""
        assert temp_db.conn is not None
        assert temp_db.db_path == "test_meeting_integration.db"

    def test_schema_exists(self, temp_db):
        """Test that all required tables exist"""
        # Try to query each table
        import db_func
        # Should not raise exceptions
        db_func.select(temp_db.conn, [], None, None, "meetings")
        db_func.select(temp_db.conn, [], None, None, "key_points")
        db_func.select(temp_db.conn, [], None, None, "action_items")
        db_func.select(temp_db.conn, [], None, None, "decisions")


class TestSaveMeeting:
    """Test saving meetings to database"""

    def test_save_basic_meeting(self, temp_db):
        """Test saving a meeting with all fields"""
        meeting_id = temp_db.save_meeting(
            meeting_id="test123",
            title="Test Meeting",
            transcript="John: Hello\nSarah: Hi",
            summary_heading="Test Summary",
            key_points=["Point 1", "Point 2"],
            action_items=[
                {"assignee": "John", "task": "Task 1", "deadline": "Friday"}
            ],
            decisions=["Decision 1"]
        )

        assert meeting_id == "test123"

    def test_save_meeting_with_empty_lists(self, temp_db):
        """Test saving a meeting with no key points, actions, or decisions"""
        meeting_id = temp_db.save_meeting(
            meeting_id="test456",
            title="Empty Meeting",
            transcript="Short meeting",
            summary_heading="Quick Sync",
            key_points=[],
            action_items=[],
            decisions=[]
        )

        assert meeting_id == "test456"

        # Verify it can be retrieved
        retrieved = temp_db.get_meeting("test456")
        assert retrieved is not None
        assert retrieved["key_points"] == []
        assert retrieved["action_items"] == []
        assert retrieved["decisions"] == []

    def test_save_meeting_with_multiple_items(self, temp_db):
        """Test saving a meeting with multiple key points, actions, and decisions"""
        meeting_id = temp_db.save_meeting(
            meeting_id="test789",
            title="Big Meeting",
            transcript="Long discussion",
            summary_heading="Comprehensive Review",
            key_points=["Point 1", "Point 2", "Point 3", "Point 4"],
            action_items=[
                {"assignee": "Alice", "task": "Task A", "deadline": "Monday"},
                {"assignee": "Bob", "task": "Task B", "deadline": "Tuesday"},
                {"assignee": "Carol", "task": "Task C", "deadline": None}
            ],
            decisions=["Decision A", "Decision B", "Decision C"]
        )

        assert meeting_id == "test789"

        # Verify order is preserved
        retrieved = temp_db.get_meeting("test789")
        assert len(retrieved["key_points"]) == 4
        assert len(retrieved["action_items"]) == 3
        assert len(retrieved["decisions"]) == 3
        assert retrieved["key_points"][0] == "Point 1"
        assert retrieved["action_items"][0]["assignee"] == "Alice"
        assert retrieved["decisions"][2] == "Decision C"


class TestGetMeeting:
    """Test retrieving meetings from database"""

    def test_get_existing_meeting(self, temp_db):
        """Test retrieving a meeting that exists"""
        # Save first
        temp_db.save_meeting(
            meeting_id="get_test_1",
            title="Retrievable Meeting",
            transcript="Test transcript",
            summary_heading="Summary",
            key_points=["Point"],
            action_items=[{"assignee": "Test", "task": "Do something", "deadline": None}],
            decisions=[]
        )

        # Retrieve
        meeting = temp_db.get_meeting("get_test_1")
        assert meeting is not None
        assert meeting["id"] == "get_test_1"
        assert meeting["title"] == "Retrievable Meeting"
        assert meeting["transcript"] == "Test transcript"
        assert len(meeting["key_points"]) == 1
        assert len(meeting["action_items"]) == 1

    def test_get_nonexistent_meeting(self, temp_db):
        """Test retrieving a meeting that doesn't exist"""
        meeting = temp_db.get_meeting("does_not_exist")
        assert meeting is None

    def test_get_meeting_preserves_order(self, temp_db):
        """Test that items are returned in the correct order"""
        temp_db.save_meeting(
            meeting_id="order_test",
            title="Order Test",
            transcript="Test",
            summary_heading="Test",
            key_points=["First", "Second", "Third"],
            action_items=[
                {"assignee": "A", "task": "Task 1", "deadline": None},
                {"assignee": "B", "task": "Task 2", "deadline": None},
                {"assignee": "C", "task": "Task 3", "deadline": None}
            ],
            decisions=["Dec 1", "Dec 2"]
        )

        meeting = temp_db.get_meeting("order_test")
        assert meeting["key_points"] == ["First", "Second", "Third"]
        assert meeting["action_items"][0]["assignee"] == "A"
        assert meeting["action_items"][1]["assignee"] == "B"
        assert meeting["action_items"][2]["assignee"] == "C"
        assert meeting["decisions"] == ["Dec 1", "Dec 2"]


class TestGetAllMeetings:
    """Test retrieving all meetings with pagination"""

    def test_get_all_empty_database(self, temp_db):
        """Test getting all meetings from an empty database"""
        meetings = temp_db.get_all_meetings()
        assert meetings == []

    def test_get_all_meetings_no_pagination(self, temp_db):
        """Test getting all meetings without pagination"""
        # Add 3 meetings
        for i in range(3):
            temp_db.save_meeting(
                meeting_id=f"meeting_{i}",
                title=f"Meeting {i}",
                transcript=f"Transcript {i}",
                summary_heading=f"Summary {i}",
                key_points=[f"Point {i}"],
                action_items=[],
                decisions=[]
            )

        meetings = temp_db.get_all_meetings()
        assert len(meetings) == 3

    def test_get_all_meetings_with_limit(self, temp_db):
        """Test pagination with limit"""
        # Add 10 meetings
        for i in range(10):
            temp_db.save_meeting(
                meeting_id=f"meeting_{i}",
                title=f"Meeting {i}",
                transcript=f"Transcript {i}",
                summary_heading=f"Summary {i}",
                key_points=[],
                action_items=[],
                decisions=[]
            )

        # Get first 5
        page1 = temp_db.get_all_meetings(limit=5, offset=0)
        assert len(page1) == 5

        # Get next 5
        page2 = temp_db.get_all_meetings(limit=5, offset=5)
        assert len(page2) == 5

        # Verify they're different
        page1_ids = [m["id"] for m in page1]
        page2_ids = [m["id"] for m in page2]
        assert len(set(page1_ids) & set(page2_ids)) == 0

    def test_get_all_meetings_ordering(self, temp_db):
        """Test that meetings are returned in correct order (newest first)"""
        import time
        # Add meetings with slight delay to ensure different timestamps
        for i in range(3):
            temp_db.save_meeting(
                meeting_id=f"meeting_{i}",
                title=f"Meeting {i}",
                transcript=f"Transcript {i}",
                summary_heading=f"Summary {i}",
                key_points=[],
                action_items=[],
                decisions=[],
                created_at=f"2024-01-{i+1:02d}T10:00:00Z"
            )
            time.sleep(0.01)

        meetings = temp_db.get_all_meetings()
        # Should be ordered newest first (DESC)
        # Since we specified created_at, meeting_2 should be first
        assert meetings[0]["id"] == "meeting_2"
        assert meetings[1]["id"] == "meeting_1"
        assert meetings[2]["id"] == "meeting_0"


class TestCountMeetings:
    """Test counting meetings in database"""

    def test_count_empty_database(self, temp_db):
        """Test count on empty database"""
        assert temp_db.count_meetings() == 0

    def test_count_after_adding(self, temp_db):
        """Test count after adding meetings"""
        # Add 7 meetings
        for i in range(7):
            temp_db.save_meeting(
                meeting_id=f"meeting_{i}",
                title=f"Meeting {i}",
                transcript="",
                summary_heading="",
                key_points=[],
                action_items=[],
                decisions=[]
            )

        assert temp_db.count_meetings() == 7


class TestDeleteMeeting:
    """Test deleting meetings"""

    def test_delete_existing_meeting(self, temp_db):
        """Test deleting a meeting that exists"""
        # Save meeting
        temp_db.save_meeting(
            meeting_id="delete_me",
            title="To Delete",
            transcript="",
            summary_heading="",
            key_points=["Point"],
            action_items=[{"assignee": "A", "task": "B", "deadline": None}],
            decisions=["Dec"]
        )

        # Verify it exists
        assert temp_db.get_meeting("delete_me") is not None
        assert temp_db.count_meetings() == 1

        # Delete
        result = temp_db.delete_meeting("delete_me")
        assert result is True

        # Verify it's gone
        assert temp_db.get_meeting("delete_me") is None
        assert temp_db.count_meetings() == 0

    def test_delete_nonexistent_meeting(self, temp_db):
        """Test deleting a meeting that doesn't exist"""
        result = temp_db.delete_meeting("does_not_exist")
        assert result is False

    def test_delete_cascades_to_related_records(self, temp_db):
        """Test that deleting a meeting also deletes related records"""
        import db_func

        # Save meeting with related data
        temp_db.save_meeting(
            meeting_id="cascade_test",
            title="Cascade Test",
            transcript="",
            summary_heading="",
            key_points=["Point 1", "Point 2"],
            action_items=[
                {"assignee": "A", "task": "Task", "deadline": None}
            ],
            decisions=["Decision"]
        )

        # Verify related records exist
        points = db_func.select(
            temp_db.conn,
            [],
            {"meeting_id": "cascade_test"},
            None,
            "key_points"
        )
        assert len(points) == 2

        # Delete meeting
        temp_db.delete_meeting("cascade_test")

        # Verify related records are gone
        points = db_func.select(
            temp_db.conn,
            [],
            {"meeting_id": "cascade_test"},
            None,
            "key_points"
        )
        assert len(points) == 0


class TestDataIntegrity:
    """Test data integrity and edge cases"""

    def test_special_characters_in_text(self, temp_db):
        """Test that special characters are handled correctly"""
        special_text = "Test with 'quotes', \"double quotes\", and\nnewlines"

        temp_db.save_meeting(
            meeting_id="special_chars",
            title="Special Characters",
            transcript=special_text,
            summary_heading="Summary",
            key_points=[special_text],
            action_items=[{"assignee": "Test", "task": special_text, "deadline": None}],
            decisions=[special_text]
        )

        meeting = temp_db.get_meeting("special_chars")
        assert meeting["transcript"] == special_text
        assert meeting["key_points"][0] == special_text
        assert meeting["action_items"][0]["task"] == special_text
        assert meeting["decisions"][0] == special_text

    def test_empty_strings(self, temp_db):
        """Test that empty strings are handled correctly"""
        temp_db.save_meeting(
            meeting_id="empty_test",
            title="",
            transcript="",
            summary_heading="",
            key_points=[""],
            action_items=[{"assignee": "", "task": "", "deadline": ""}],
            decisions=[""]
        )

        meeting = temp_db.get_meeting("empty_test")
        assert meeting["title"] == ""
        assert meeting["transcript"] == ""

    def test_none_values_in_action_items(self, temp_db):
        """Test that None values in action items are handled correctly"""
        temp_db.save_meeting(
            meeting_id="none_test",
            title="None Test",
            transcript="Test",
            summary_heading="Test",
            key_points=[],
            action_items=[
                {"assignee": "Test", "task": "Do something", "deadline": None}
            ],
            decisions=[]
        )

        meeting = temp_db.get_meeting("none_test")
        assert meeting["action_items"][0]["deadline"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
