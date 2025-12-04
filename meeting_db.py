"""
Meeting Database Module
Handles persistent storage of meeting records using SQLite via db_func
"""

import db_func
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class MeetingDatabase:
    """
    Database wrapper for meeting storage with proper schema management
    """

    def __init__(self, db_path: str = "meetings.db"):
        """
        Initialize the meeting database

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = db_func.connect_database(db_path)
        self._init_schema()

    def _init_schema(self):
        """
        Initialize database schema if tables don't exist
        Creates: meetings, key_points, action_items, decisions tables
        """
        # Check if tables exist by trying to query them
        try:
            db_func.select(self.conn, [], None, None, "meetings")
        except:
            # Tables don't exist, create them
            self._create_tables()

    def _create_tables(self):
        """Create all required tables with proper schema"""

        # Meetings table - main meeting metadata
        meetings_spec = {
            "id": ["TEXT", "NOT NULL"],
            "created_at": ["TEXT", "NOT NULL"],
            "title": ["TEXT", "NOT NULL"],
            "transcript": ["TEXT"],
            "summary_heading": ["TEXT"],
            "Primary Key": "id",
        }
        db_func.create_table(self.conn, meetings_spec, "meetings")

        # Key points table - one-to-many with meetings
        key_points_spec = {
            "id": ["INTEGER", "NOT NULL"],
            "meeting_id": ["TEXT", "NOT NULL"],
            "point": ["TEXT", "NOT NULL"],
            "point_order": ["INTEGER", "NOT NULL"],
            "Primary Key": "id",
            "Foreign Key": [("meeting_id", "meetings")],
        }
        db_func.create_table(self.conn, key_points_spec, "key_points")

        # Action items table - one-to-many with meetings
        action_items_spec = {
            "id": ["INTEGER", "NOT NULL"],
            "meeting_id": ["TEXT", "NOT NULL"],
            "assignee": ["TEXT"],
            "task": ["TEXT", "NOT NULL"],
            "deadline": ["TEXT"],
            "item_order": ["INTEGER", "NOT NULL"],
            "Primary Key": "id",
            "Foreign Key": [("meeting_id", "meetings")],
        }
        db_func.create_table(self.conn, action_items_spec, "action_items")

        # Decisions table - one-to-many with meetings
        decisions_spec = {
            "id": ["INTEGER", "NOT NULL"],
            "meeting_id": ["TEXT", "NOT NULL"],
            "decision": ["TEXT", "NOT NULL"],
            "decision_order": ["INTEGER", "NOT NULL"],
            "Primary Key": "id",
            "Foreign Key": [("meeting_id", "meetings")],
        }
        db_func.create_table(self.conn, decisions_spec, "decisions")

    def save_meeting(
        self,
        meeting_id: str,
        title: str,
        transcript: str,
        summary_heading: str,
        key_points: List[str],
        action_items: List[Dict[str, Any]],
        decisions: List[str],
        created_at: Optional[str] = None,
    ) -> str:
        """
        Save a complete meeting record to the database

        Args:
            meeting_id: Unique meeting identifier
            title: Meeting title
            transcript: Full meeting transcript
            summary_heading: Summary heading text
            key_points: List of key discussion points
            action_items: List of action item dicts with assignee, task, deadline
            decisions: List of decisions made
            created_at: ISO timestamp (defaults to current time)

        Returns:
            The meeting_id that was saved
        """
        if created_at is None:
            created_at = (
                datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            )

        # Insert main meeting record
        meeting_data = {
            "id": meeting_id,
            "created_at": created_at,
            "title": title,
            "transcript": transcript,
            "summary_heading": summary_heading,
        }
        db_func.single_insert(self.conn, meeting_data, "meetings")

        # Insert key points
        for idx, point in enumerate(key_points):
            point_data = {"meeting_id": meeting_id, "point": point, "point_order": idx}
            db_func.single_insert(self.conn, point_data, "key_points")

        # Insert action items
        for idx, item in enumerate(action_items):
            action_data = {
                "meeting_id": meeting_id,
                "assignee": item.get("assignee", "Unassigned"),
                "task": item.get("task", ""),
                "deadline": item.get("deadline"),
                "item_order": idx,
            }
            db_func.single_insert(self.conn, action_data, "action_items")

        # Insert decisions
        for idx, decision in enumerate(decisions):
            decision_data = {"meeting_id": meeting_id, "decision": decision, "decision_order": idx}
            db_func.single_insert(self.conn, decision_data, "decisions")

        return meeting_id

    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a complete meeting record by ID

        Args:
            meeting_id: The meeting ID to retrieve

        Returns:
            Dictionary with meeting data or None if not found
        """
        # Get main meeting record
        meetings = db_func.select(self.conn, [], {"id": meeting_id}, None, "meetings")

        if not meetings:
            return None

        # Convert to dict and normalize keys to lowercase
        meeting = {k.lower(): v for k, v in dict(meetings[0]).items()}

        # Get key points (note: db_func uppercases all column names)
        points_rows = db_func.select(
            self.conn, [], {"meeting_id": meeting_id}, "point_order", "key_points"
        )
        meeting["key_points"] = [dict(row)["POINT"] for row in points_rows]

        # Get action items
        action_rows = db_func.select(
            self.conn, [], {"meeting_id": meeting_id}, "item_order", "action_items"
        )
        meeting["action_items"] = [
            {
                "assignee": dict(row)["ASSIGNEE"],
                "task": dict(row)["TASK"],
                "deadline": dict(row)["DEADLINE"],
            }
            for row in action_rows
        ]

        # Get decisions
        decision_rows = db_func.select(
            self.conn, [], {"meeting_id": meeting_id}, "decision_order", "decisions"
        )
        meeting["decisions"] = [dict(row)["DECISION"] for row in decision_rows]

        return meeting

    def get_all_meetings(
        self, limit: Optional[int] = None, offset: int = 0, order_by: str = "created_at DESC"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all meetings with optional pagination

        Args:
            limit: Maximum number of meetings to return (None = all)
            offset: Number of meetings to skip
            order_by: SQL ORDER BY clause (default: newest first)

        Returns:
            List of meeting dictionaries with all related data
        """
        # Build query with pagination
        if limit is not None:
            order_clause = f"{order_by} LIMIT {limit} OFFSET {offset}"
        else:
            order_clause = order_by

        # Get meetings
        meeting_rows = db_func.select(self.conn, [], None, order_clause, "meetings")

        # For each meeting, fetch related data
        meetings = []
        for row in meeting_rows:
            # Convert to dict and normalize keys to lowercase
            meeting_dict = {k.lower(): v for k, v in dict(row).items()}
            meeting_id = meeting_dict["id"]

            # Get key points (note: db_func uppercases all column names)
            points_rows = db_func.select(
                self.conn, [], {"meeting_id": meeting_id}, "point_order", "key_points"
            )
            meeting_dict["key_points"] = [dict(r)["POINT"] for r in points_rows]

            # Get action items
            action_rows = db_func.select(
                self.conn, [], {"meeting_id": meeting_id}, "item_order", "action_items"
            )
            meeting_dict["action_items"] = [
                {
                    "assignee": dict(r)["ASSIGNEE"],
                    "task": dict(r)["TASK"],
                    "deadline": dict(r)["DEADLINE"],
                }
                for r in action_rows
            ]

            # Get decisions
            decision_rows = db_func.select(
                self.conn, [], {"meeting_id": meeting_id}, "decision_order", "decisions"
            )
            meeting_dict["decisions"] = [dict(r)["DECISION"] for r in decision_rows]

            meetings.append(meeting_dict)

        return meetings

    def count_meetings(self) -> int:
        """
        Get total count of meetings in database

        Returns:
            Total number of meetings
        """
        meetings = db_func.select(self.conn, [], None, None, "meetings")
        return len(meetings)

    def delete_meeting(self, meeting_id: str) -> bool:
        """
        Delete a meeting and all related records

        Args:
            meeting_id: ID of meeting to delete

        Returns:
            True if meeting was deleted, False if not found
        """
        # Delete related records (foreign key constraints will cascade)
        db_func.delete(self.conn, {"meeting_id": meeting_id}, "key_points")
        db_func.delete(self.conn, {"meeting_id": meeting_id}, "action_items")
        db_func.delete(self.conn, {"meeting_id": meeting_id}, "decisions")

        # Delete main meeting record
        deleted_count = db_func.delete(self.conn, {"id": meeting_id}, "meetings")
        return deleted_count > 0

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()


# Example usage
if __name__ == "__main__":
    print("=== Meeting Database Test ===\n")

    # Create database
    db = MeetingDatabase("test_meetings.db")

    # Save a test meeting
    meeting_id = "20241124120000"
    db.save_meeting(
        meeting_id=meeting_id,
        title="Sprint Planning",
        transcript="John: Let's discuss the sprint.\nSarah: I'll work on the frontend.",
        summary_heading="Sprint Planning - Week 5",
        key_points=["Discussed sprint goals", "Assigned tasks to team members"],
        action_items=[
            {"assignee": "Sarah", "task": "Implement login UI", "deadline": "Friday"},
            {"assignee": "Mike", "task": "Setup OAuth", "deadline": "Wednesday"},
        ],
        decisions=["Using OAuth for authentication", "Targeting Friday release"],
    )
    print(f"✓ Saved meeting {meeting_id}")

    # Retrieve the meeting
    retrieved = db.get_meeting(meeting_id)
    print(f"\n✓ Retrieved meeting: {retrieved['title']}")
    print(f"  - Key points: {len(retrieved['key_points'])}")
    print(f"  - Action items: {len(retrieved['action_items'])}")
    print(f"  - Decisions: {len(retrieved['decisions'])}")

    # Get all meetings
    all_meetings = db.get_all_meetings(limit=10)
    print(f"\n✓ Total meetings in database: {len(all_meetings)}")

    # Clean up
    db.close()
    print("\n✓ Database test complete!")
