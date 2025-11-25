'''
End-to-end test for database persistence across app restarts
Simulates the full workflow: save -> close -> reopen -> verify
'''

import os
from meeting_db import MeetingDatabase


def test_persistence_across_restarts():
    """
    Test that meetings persist across database close/reopen cycles
    Simulates restarting the Streamlit app
    """
    db_path = "test_e2e_persistence.db"

    # Clean up any existing test database
    if os.path.exists(db_path):
        os.remove(db_path)

    print("=== End-to-End Persistence Test ===\n")

    # Step 1: First "app session" - create database and save meetings
    print("Step 1: First session - Creating database and saving meetings...")
    db1 = MeetingDatabase(db_path)

    # Save 3 test meetings
    meetings_data = [
        {
            "meeting_id": "20241124120000",
            "title": "Sprint Planning",
            "transcript": "John: Let's plan the sprint.\nSarah: I'll work on the frontend.",
            "summary_heading": "Sprint Planning - Week 5",
            "key_points": ["Discussed sprint goals", "Assigned tasks"],
            "action_items": [
                {"assignee": "Sarah", "task": "Implement login UI", "deadline": "Friday"},
                {"assignee": "Mike", "task": "Setup OAuth", "deadline": "Wednesday"}
            ],
            "decisions": ["Using OAuth for authentication"]
        },
        {
            "meeting_id": "20241124130000",
            "title": "Daily Standup",
            "transcript": "Quick standup updates",
            "summary_heading": "Daily Standup",
            "key_points": ["Team updates", "Blockers discussed"],
            "action_items": [],
            "decisions": []
        },
        {
            "meeting_id": "20241124140000",
            "title": "Design Review",
            "transcript": "Reviewed new UI mockups",
            "summary_heading": "Design Review Meeting",
            "key_points": ["Reviewed mockups", "Discussed color scheme", "Agreed on layout"],
            "action_items": [
                {"assignee": "Designer", "task": "Update mockups", "deadline": "Tomorrow"}
            ],
            "decisions": ["Approved new color scheme", "Layout finalized"]
        }
    ]

    for meeting in meetings_data:
        db1.save_meeting(**meeting)
        print(f"  ✓ Saved: {meeting['title']}")

    # Verify count
    count = db1.count_meetings()
    print(f"\n  Total meetings in database: {count}")
    assert count == 3, f"Expected 3 meetings, got {count}"

    # Close the database (simulating app shutdown)
    print("\nStep 2: Closing database (simulating app shutdown)...")
    db1.close()
    print("  ✓ Database closed")

    # Step 2: Second "app session" - reopen database and verify data persists
    print("\nStep 3: Second session - Reopening database...")
    db2 = MeetingDatabase(db_path)
    print("  ✓ Database reopened")

    # Verify count is still 3
    count = db2.count_meetings()
    print(f"\n  Total meetings in database: {count}")
    assert count == 3, f"Expected 3 meetings after reopen, got {count}"

    # Retrieve all meetings
    all_meetings = db2.get_all_meetings()
    print(f"\n  Retrieved {len(all_meetings)} meetings")

    # Verify first meeting data in detail
    meeting1 = db2.get_meeting("20241124120000")
    assert meeting1 is not None, "Meeting 1 should exist"
    assert meeting1["title"] == "Sprint Planning", "Title mismatch"
    assert len(meeting1["key_points"]) == 2, "Key points count mismatch"
    assert len(meeting1["action_items"]) == 2, "Action items count mismatch"
    assert len(meeting1["decisions"]) == 1, "Decisions count mismatch"
    print("  ✓ Meeting 1 verified: all data intact")

    # Verify second meeting
    meeting2 = db2.get_meeting("20241124130000")
    assert meeting2 is not None, "Meeting 2 should exist"
    assert meeting2["title"] == "Daily Standup", "Title mismatch"
    assert len(meeting2["action_items"]) == 0, "Should have no action items"
    print("  ✓ Meeting 2 verified: all data intact")

    # Verify third meeting
    meeting3 = db2.get_meeting("20241124140000")
    assert meeting3 is not None, "Meeting 3 should exist"
    assert meeting3["title"] == "Design Review", "Title mismatch"
    assert len(meeting3["decisions"]) == 2, "Decisions count mismatch"
    print("  ✓ Meeting 3 verified: all data intact")

    # Test pagination
    print("\nStep 4: Testing pagination...")
    page1 = db2.get_all_meetings(limit=2, offset=0)
    assert len(page1) == 2, "First page should have 2 meetings"
    print(f"  ✓ Page 1: {len(page1)} meetings")

    page2 = db2.get_all_meetings(limit=2, offset=2)
    assert len(page2) == 1, "Second page should have 1 meeting"
    print(f"  ✓ Page 2: {len(page2)} meeting")

    # Test deletion and persistence
    print("\nStep 5: Testing deletion...")
    deleted = db2.delete_meeting("20241124130000")
    assert deleted is True, "Deletion should succeed"
    print("  ✓ Deleted meeting: Daily Standup")

    count = db2.count_meetings()
    assert count == 2, f"Expected 2 meetings after deletion, got {count}"
    print(f"  ✓ Count after deletion: {count}")

    # Close again
    db2.close()
    print("\nStep 6: Closing database again...")

    # Reopen and verify deletion persisted
    print("\nStep 7: Reopening to verify deletion persisted...")
    db3 = MeetingDatabase(db_path)
    count = db3.count_meetings()
    assert count == 2, f"Expected 2 meetings after reopen, got {count}"
    print(f"  ✓ Count after reopen: {count}")

    # Verify deleted meeting is gone
    deleted_meeting = db3.get_meeting("20241124130000")
    assert deleted_meeting is None, "Deleted meeting should not exist"
    print("  ✓ Deleted meeting confirmed gone")

    # Verify other meetings still exist
    meeting1_again = db3.get_meeting("20241124120000")
    meeting3_again = db3.get_meeting("20241124140000")
    assert meeting1_again is not None, "Meeting 1 should still exist"
    assert meeting3_again is not None, "Meeting 3 should still exist"
    print("  ✓ Other meetings still exist")

    # Cleanup
    db3.close()
    if os.path.exists(db_path):
        os.remove(db_path)

    print("\n" + "=" * 50)
    print("✅ END-TO-END PERSISTENCE TEST PASSED")
    print("=" * 50)
    print("\nConclusion: Data successfully persists across:")
    print("  - Database close/reopen cycles")
    print("  - Multiple app sessions")
    print("  - Delete operations")
    print("\nThe app will maintain meeting history across restarts!")


if __name__ == "__main__":
    try:
        test_persistence_across_restarts()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
