"""
test_models.py

Unit tests for:
 - meeting_record.MeetingRecord
 - class_helpers.* (smoke tests)
 - user.User (init, add_meeting, remove_meeting, update_meeting, delete_user)

Run:
    python -m unittest test_models.py
"""

import json
import unittest
from unittest.mock import patch, MagicMock

import meeting_record as mr_mod
import class_helpers as ch_mod
import user as user_mod


class TestMeetingRecord(unittest.TestCase):
    def test_meetingrecord_from_ollama_input(self):
        incoming = {
            "summary_heading": "Weekly sync",
            "key_points": ["kp1", "kp2"],
            "action_items": [
                {"assignee": "alice", "task": "write report", "deadline": "2025-11-01", "status": "open"}
            ]
        }
        rec = mr_mod.MeetingRecord(incoming, ollama=True)
        self.assertEqual(rec.summary_heading, "Weekly sync")
        self.assertEqual(rec.key_points, ["kp1", "kp2"])
        encoded = rec.format_for_insert()
        # values should be JSON strings
        self.assertIsInstance(encoded["summary_heading"], str)
        json.loads(encoded["summary_heading"])

    def test_meetingrecord_from_db_row(self):
        db_row = {
            "meeting_id": json.dumps(5),
            "meeting_date": json.dumps("2025-10-29"),
            "summary_heading": json.dumps("Retro"),
            "key_points": json.dumps(["done", "todo"]),
            "action_items": json.dumps([{"assignee":"bob","task":"clean","deadline":"2025-12-01","status":"open"}])
        }
        rec = mr_mod.MeetingRecord(db_row, ollama=False)
        self.assertEqual(rec.summary_heading, "Retro")
        self.assertEqual(rec.key_points, ["done", "todo"])
        self.assertIsInstance(rec.action_items, list)
        self.assertEqual(rec.action_items[0]["assignee"], "bob")


class TestUserInitAndCRUD(unittest.TestCase):
    def setUp(self):
        self.conn = object()

    def test_init_existing_user_loads_meetings(self):
        # DB-style row: include user_id and meeting fields. meeting_id might be JSON-encoded.
        sample_db_row = {
            "user_id": 2,
            "meeting_id": json.dumps(10),
            "meeting_date": json.dumps("2025-10-28"),
            "summary_heading": json.dumps("Standup"),
            "key_points": json.dumps(["kp"]),
            "action_items": json.dumps([{"assignee":"carol","task":"t","deadline":"2025-11-05","status":"open"}])
        }
        with patch.object(user_mod.class_helpers, 'check_username', return_value=True) as mock_check, \
             patch.object(user_mod.class_helpers, 'fetch_user_meetings', return_value=[sample_db_row]) as mock_fetch:
            u = user_mod.User(self.conn, "dave")
            mock_check.assert_called_once_with(self.conn, "dave")
            mock_fetch.assert_called_once_with(self.conn, "dave")
            self.assertEqual(u.user_id, 2)
            self.assertEqual(u.username, "dave")
            self.assertEqual(len(u.meetings), 1)
            # last_meeting_id should be at least 10
            self.assertTrue(int(u.last_meeting_id) >= 10)

    def test_init_new_user_sets_defaults(self):
        with patch.object(user_mod.class_helpers, 'check_username', return_value=False) as mock_check, \
             patch.object(user_mod.class_helpers, 'fetch_last_user_id', return_value=42) as mock_fetch_id:
            u = user_mod.User(self.conn, "newuser")
            mock_check.assert_called_once_with(self.conn, "newuser")
            mock_fetch_id.assert_called_once_with(self.conn, "newuser")
            self.assertEqual(u.user_id, 42)
            self.assertEqual(u.username, "newuser")
            self.assertEqual(u.meetings, [])
            self.assertEqual(u.last_meeting_id, 0)

    def test_add_meeting_appends_and_calls_insert(self):
        with patch.object(user_mod.class_helpers, 'check_username', return_value=False), \
             patch.object(user_mod.class_helpers, 'fetch_last_user_id', return_value=7):
            u = user_mod.User(self.conn, "alice")
            # start last_meeting_id == 0
            self.assertEqual(u.last_meeting_id, 0)

            # Prepare a transcription dict (ollama input)
            transcription = {
                "summary_heading": "Sync",
                "key_points": ["a", "b"],
                "action_items": [{"assignee":"alice","task":"do","deadline":"2025-11-30","status":"open"}]
            }

            with patch.object(user_mod.class_helpers, 'insert_meeting', autospec=True) as mock_insert:
                u.add_meeting(self.conn, transcription)
                # one meeting appended
                self.assertEqual(len(u.meetings), 1)
                # last_meeting_id incremented from 0 to 1
                self.assertEqual(u.last_meeting_id, 1)
                # insert_meeting called with connection and dict
                mock_insert.assert_called_once()
                args = mock_insert.call_args[0]
                # signature: insert_meeting(conn, insert_dict)
                self.assertEqual(args[0], self.conn)
                insert_dict = args[1]
                self.assertEqual(insert_dict["username"], "alice")
                self.assertEqual(insert_dict["user_id"], 7)
                # Ensure meeting_id key present in insert payload
                self.assertIn("meeting_id", insert_dict)

    def test_remove_meeting_calls_drop_and_removes_from_list(self):
        with patch.object(user_mod.class_helpers, 'check_username', return_value=False), \
             patch.object(user_mod.class_helpers, 'fetch_last_user_id', return_value=9):
            u = user_mod.User(self.conn, "bob")
            # add one meeting (mock insert to keep test focused)
            transcription = {"summary_heading":"X","key_points":[],"action_items":[]}
            with patch.object(user_mod.class_helpers, 'insert_meeting', autospec=True):
                u.add_meeting(self.conn, transcription)
            # Now pop it and assert drop called
            with patch.object(user_mod.class_helpers, 'drop_meeting', autospec=True) as mock_drop:
                u.remove_meeting(self.conn, 0)
                mock_drop.assert_called_once()
                self.assertEqual(len(u.meetings), 0)

    def test_update_meeting_modifies_and_calls_update(self):
        with patch.object(user_mod.class_helpers, 'check_username', return_value=False), \
             patch.object(user_mod.class_helpers, 'fetch_last_user_id', return_value=3):
            u = user_mod.User(self.conn, "chuck")
            transcription = {
                "summary_heading": "Before",
                "key_points": ["one"],
                "action_items": [{"assignee":"x","task":"t","deadline":"2025-12-01","status":"open"}]
            }
            with patch.object(user_mod.class_helpers, 'insert_meeting', autospec=True):
                u.add_meeting(self.conn, transcription)

            # update the summary_heading of meeting 0
            with patch.object(user_mod.class_helpers, 'update_meeting', autospec=True) as mock_update:
                u.update_meeting(self.conn, 0, ("summary_heading",), "After")
                mock_update.assert_called_once()
                # verify in-object update
                self.assertEqual(u.meetings[0].get_field("summary_heading"), "After")

            # update a key_point element
            with patch.object(user_mod.class_helpers, 'update_meeting', autospec=True) as mock_update2:
                # replace key_points[0] with "changed"
                u.update_meeting(self.conn, 0, ("key_points", 0), "changed")
                mock_update2.assert_called_once()
                self.assertEqual(u.meetings[0].get_field("key_points")[0], "changed")

            # update an action_item field (task)
            with patch.object(user_mod.class_helpers, 'update_meeting', autospec=True) as mock_update3:
                u.update_meeting(self.conn, 0, ("action_items", 0, "task"), "newtask")
                mock_update3.assert_called_once()
                self.assertEqual(u.meetings[0].get_field("action_items")[0]["task"], "newtask")

    def test_delete_user_calls_helper_and_resets(self):
        with patch.object(user_mod.class_helpers, 'check_username', return_value=False), \
             patch.object(user_mod.class_helpers, 'fetch_last_user_id', return_value=11):
            u = user_mod.User(self.conn, "zack")
            # add a meeting to ensure not empty
            transcription = {"summary_heading":"Y","key_points":[],"action_items":[]}
            with patch.object(user_mod.class_helpers, 'insert_meeting', autospec=True):
                u.add_meeting(self.conn, transcription)

            # capture expected values BEFORE calling delete_user
            expected_user_id = u.user_id
            expected_username = u.username

            with patch.object(user_mod.class_helpers, 'delete_user', autospec=True) as mock_delete:
                u.delete_user(self.conn)
                # ensure the helper was called with the pre-reset values
                mock_delete.assert_called_once_with(self.conn, expected_user_id, expected_username)
                # and the in-memory object is reset afterwards
                self.assertEqual(u.user_id, 0)
                self.assertEqual(u.username, "")
                self.assertEqual(u.meetings, [])


if __name__ == "__main__":
    unittest.main()

