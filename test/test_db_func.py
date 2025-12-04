"""
Unit tests for db_func.py

Tests all CRUD operations and edge cases for the SQLite database wrapper
"""

import pytest
import os
import sqlite3
from .. import db_func as db


@pytest.fixture
def test_db():
    """
    Fixture to create a clean test database for each test
    Automatically cleans up after the test completes
    """
    db_name = "test_fixture"
    db_path = f"{db_name}.db"

    # Remove existing db if any
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create fresh database
    conn = db.create_database(db_name)

    yield conn

    # Cleanup
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def test_table_spec():
    """Fixture providing a standard table specification"""
    return {
        "user_id": ["VARCHAR(255)", "NOT NULL"],
        "username": ["VARCHAR(100)"],
        "email": ["VARCHAR(255)"],
        "age": ["INTEGER"],
        "Primary Key": "user_id",
    }


class TestDatabaseCreation:
    """Tests for database creation and connection"""

    def test_create_database(self):
        """Test creating a new database"""
        db_name = "test_create"
        db_path = f"{db_name}.db"

        # Clean up if exists
        if os.path.exists(db_path):
            os.remove(db_path)

        conn = db.create_database(db_name)

        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        assert os.path.exists(db_path)

        conn.close()
        os.remove(db_path)

    def test_connect_database(self):
        """Test connecting to an existing database"""
        db_name = "test_connect"
        db_path = f"{db_name}.db"

        # Create database first
        if os.path.exists(db_path):
            os.remove(db_path)

        conn1 = db.create_database(db_name)
        conn1.close()

        # Now connect to existing database
        conn2 = db.connect_database(db_path)

        assert conn2 is not None
        assert isinstance(conn2, sqlite3.Connection)

        conn2.close()
        os.remove(db_path)


class TestTableOperations:
    """Tests for table creation and deletion"""

    def test_create_table_basic(self, test_db):
        """Test creating a table with basic columns"""
        spec = {"id": ["INTEGER"], "name": ["VARCHAR(100)"]}

        db.create_table(test_db, spec, "test_table")

        # Verify table exists
        cursor = test_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TEST_TABLE'")
        result = cursor.fetchone()
        cursor.close()

        assert result is not None
        assert result[0] == "TEST_TABLE"

    def test_create_table_with_primary_key(self, test_db, test_table_spec):
        """Test creating a table with a primary key"""
        db.create_table(test_db, test_table_spec, "users")

        # Insert should work with valid primary key
        db.single_insert(test_db, {"user_id": "U001", "username": "alice"}, "users")

        # Duplicate primary key should fail
        with pytest.raises(sqlite3.IntegrityError):
            db.single_insert(test_db, {"user_id": "U001", "username": "bob"}, "users")

    def test_create_table_with_foreign_key(self, test_db):
        """Test creating tables with foreign key relationships"""
        # Create parent table
        parent_spec = {
            "dept_id": ["VARCHAR(10)"],
            "dept_name": ["VARCHAR(100)"],
            "Primary Key": "dept_id",
        }
        db.create_table(test_db, parent_spec, "departments")

        # Create child table with foreign key
        child_spec = {
            "emp_id": ["VARCHAR(10)"],
            "emp_name": ["VARCHAR(100)"],
            "dept_id": ["VARCHAR(10)"],
            "Primary Key": "emp_id",
            "Foreign Key": [("dept_id", "departments")],
        }
        db.create_table(test_db, child_spec, "employees")

        # Verify both tables exist
        cursor = test_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()

        assert "DEPARTMENTS" in tables
        assert "EMPLOYEES" in tables

    def test_drop_table(self, test_db):
        """Test dropping a table"""
        spec = {"id": ["INTEGER"], "name": ["VARCHAR(100)"]}
        db.create_table(test_db, spec, "temp_table")

        # Verify table exists
        cursor = test_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TEMP_TABLE'")
        assert cursor.fetchone() is not None
        cursor.close()

        # Drop the table
        db.drop_table(test_db, "temp_table")

        # Verify table no longer exists
        cursor = test_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TEMP_TABLE'")
        assert cursor.fetchone() is None
        cursor.close()

    def test_drop_nonexistent_table(self, test_db):
        """Test that dropping a non-existent table doesn't raise an error"""
        # Should not raise an error due to IF EXISTS
        db.drop_table(test_db, "nonexistent_table")


class TestInsertOperations:
    """Tests for INSERT operations"""

    def test_single_insert_basic(self, test_db, test_table_spec):
        """Test basic single row insertion"""
        db.create_table(test_db, test_table_spec, "users")

        row = {"user_id": "U001", "username": "alice", "email": "alice@example.com", "age": 25}

        db.single_insert(test_db, row, "users")

        # Verify insertion
        rows = db.select(test_db, None, {"user_id": "U001"}, None, "users")
        assert len(rows) == 1
        assert rows[0]["USERNAME"] == "alice"

    def test_single_insert_partial_columns(self, test_db, test_table_spec):
        """Test inserting with only some columns"""
        db.create_table(test_db, test_table_spec, "users")

        row = {
            "user_id": "U002",
            "username": "bob",
            # email and age omitted
        }

        db.single_insert(test_db, row, "users")

        rows = db.select(test_db, None, {"user_id": "U002"}, None, "users")
        assert len(rows) == 1
        assert rows[0]["USERNAME"] == "bob"
        assert rows[0]["EMAIL"] is None

    def test_single_insert_case_insensitive(self, test_db, test_table_spec):
        """Test that column names are case-insensitive"""
        db.create_table(test_db, test_table_spec, "users")

        row = {
            "USER_ID": "U003",  # Uppercase
            "UserName": "charlie",  # Mixed case
            "email": "charlie@example.com",  # Lowercase
        }

        db.single_insert(test_db, row, "users")

        rows = db.select(test_db, None, {"user_id": "U003"}, None, "users")
        assert len(rows) == 1


class TestSelectOperations:
    """Tests for SELECT operations"""

    @pytest.fixture
    def populated_table(self, test_db, test_table_spec):
        """Fixture with a populated table"""
        db.create_table(test_db, test_table_spec, "users")

        users = [
            {"user_id": "U001", "username": "alice", "email": "alice@example.com", "age": 25},
            {"user_id": "U002", "username": "bob", "email": "bob@example.com", "age": 30},
            {"user_id": "U003", "username": "charlie", "email": "charlie@example.com", "age": 25},
        ]

        for user in users:
            db.single_insert(test_db, user, "users")

        return test_db

    def test_select_all(self, populated_table):
        """Test selecting all rows"""
        rows = db.select(populated_table, None, None, None, "users")
        assert len(rows) == 3

    def test_select_specific_columns(self, populated_table):
        """Test selecting specific columns"""
        rows = db.select(populated_table, ["user_id", "username"], None, None, "users")

        assert len(rows) == 3
        # All rows should have these columns
        for row in rows:
            assert "USER_ID" in row.keys()
            assert "USERNAME" in row.keys()

    def test_select_with_where_dict(self, populated_table):
        """Test SELECT with WHERE clause as dictionary"""
        rows = db.select(populated_table, None, {"username": "alice"}, None, "users")

        assert len(rows) == 1
        assert rows[0]["USERNAME"] == "alice"

    def test_select_with_where_multiple_conditions(self, populated_table):
        """Test SELECT with multiple WHERE conditions (AND)"""
        rows = db.select(populated_table, None, {"username": "alice", "age": 25}, None, "users")

        assert len(rows) == 1
        assert rows[0]["USERNAME"] == "alice"

    def test_select_with_where_string(self, populated_table):
        """Test SELECT with WHERE clause as raw SQL string"""
        rows = db.select(populated_table, None, "AGE > 25", None, "users")

        assert len(rows) == 1
        assert rows[0]["USERNAME"] == "bob"

    def test_select_with_order_by_string(self, populated_table):
        """Test SELECT with ORDER BY as string"""
        rows = db.select(populated_table, None, None, "age DESC", "users")

        assert len(rows) == 3
        assert rows[0]["AGE"] == 30  # Bob should be first

    def test_select_with_order_by_list(self, populated_table):
        """Test SELECT with ORDER BY as list"""
        rows = db.select(populated_table, None, None, ["age", "username"], "users")

        assert len(rows) == 3
        # Age 25 rows should come first, then ordered by username
        assert rows[0]["USERNAME"] == "alice"
        assert rows[1]["USERNAME"] == "charlie"

    def test_select_no_results(self, populated_table):
        """Test SELECT that returns no results"""
        rows = db.select(populated_table, None, {"username": "nonexistent"}, None, "users")
        assert len(rows) == 0


class TestUpdateOperations:
    """Tests for UPDATE operations"""

    @pytest.fixture
    def populated_table(self, test_db, test_table_spec):
        """Fixture with a populated table"""
        db.create_table(test_db, test_table_spec, "users")

        users = [
            {"user_id": "U001", "username": "alice", "email": "alice@example.com", "age": 25},
            {"user_id": "U002", "username": "bob", "email": "bob@example.com", "age": 30},
        ]

        for user in users:
            db.single_insert(test_db, user, "users")

        return test_db

    def test_update_single_row(self, populated_table):
        """Test updating a single row"""
        affected = db.update(
            populated_table, {"email": "alice.new@example.com"}, {"user_id": "U001"}, "users"
        )

        assert affected == 1

        # Verify update
        rows = db.select(populated_table, None, {"user_id": "U001"}, None, "users")
        assert rows[0]["EMAIL"] == "alice.new@example.com"

    def test_update_multiple_columns(self, populated_table):
        """Test updating multiple columns at once"""
        affected = db.update(
            populated_table, {"username": "alice_updated", "age": 26}, {"user_id": "U001"}, "users"
        )

        assert affected == 1

        # Verify update
        rows = db.select(populated_table, None, {"user_id": "U001"}, None, "users")
        assert rows[0]["USERNAME"] == "alice_updated"
        assert rows[0]["AGE"] == 26

    def test_update_multiple_rows(self, populated_table):
        """Test updating multiple rows at once"""
        # First add a row with same age
        db.single_insert(
            populated_table, {"user_id": "U003", "username": "charlie", "age": 25}, "users"
        )

        # Update all users with age 25
        affected = db.update(populated_table, {"age": 26}, {"age": 25}, "users")

        assert affected == 2  # alice and charlie

    def test_update_with_string_where(self, populated_table):
        """Test UPDATE with WHERE clause as raw SQL string"""
        affected = db.update(populated_table, {"age": 31}, "AGE = 30", "users")

        assert affected == 1

    def test_update_no_where(self, populated_table):
        """Test UPDATE without WHERE clause (updates all rows)"""
        affected = db.update(populated_table, {"email": "updated@example.com"}, None, "users")

        assert affected == 2  # Both rows updated

        # Verify all rows updated
        rows = db.select(populated_table, None, None, None, "users")
        for row in rows:
            assert row["EMAIL"] == "updated@example.com"

    def test_update_no_match(self, populated_table):
        """Test UPDATE with WHERE that matches no rows"""
        affected = db.update(
            populated_table, {"email": "new@example.com"}, {"user_id": "U999"}, "users"
        )

        assert affected == 0


class TestDeleteOperations:
    """Tests for DELETE operations"""

    @pytest.fixture
    def populated_table(self, test_db, test_table_spec):
        """Fixture with a populated table"""
        db.create_table(test_db, test_table_spec, "users")

        users = [
            {"user_id": "U001", "username": "alice", "age": 25},
            {"user_id": "U002", "username": "bob", "age": 30},
            {"user_id": "U003", "username": "charlie", "age": 25},
        ]

        for user in users:
            db.single_insert(test_db, user, "users")

        return test_db

    def test_delete_single_row(self, populated_table):
        """Test deleting a single row"""
        deleted = db.delete(populated_table, {"user_id": "U001"}, "users")

        assert deleted == 1

        # Verify deletion
        rows = db.select(populated_table, None, None, None, "users")
        assert len(rows) == 2

    def test_delete_multiple_rows(self, populated_table):
        """Test deleting multiple rows"""
        deleted = db.delete(populated_table, {"age": 25}, "users")

        assert deleted == 2  # alice and charlie

        # Verify deletion
        rows = db.select(populated_table, None, None, None, "users")
        assert len(rows) == 1
        assert rows[0]["USERNAME"] == "bob"

    def test_delete_with_string_where(self, populated_table):
        """Test DELETE with WHERE clause as raw SQL string"""
        deleted = db.delete(populated_table, "AGE > 25", "users")

        assert deleted == 1  # Only bob

    def test_delete_all_rows(self, populated_table):
        """Test DELETE without WHERE clause (deletes all rows)"""
        deleted = db.delete(populated_table, None, "users")

        assert deleted == 3

        # Verify all deleted
        rows = db.select(populated_table, None, None, None, "users")
        assert len(rows) == 0

    def test_delete_no_match(self, populated_table):
        """Test DELETE with WHERE that matches no rows"""
        deleted = db.delete(populated_table, {"user_id": "U999"}, "users")

        assert deleted == 0


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_special_characters_in_data(self, test_db, test_table_spec):
        """Test handling of special characters in data"""
        db.create_table(test_db, test_table_spec, "users")

        row = {
            "user_id": "U001",
            "username": "alice's account",  # Single quote
            "email": "alice+test@example.com",  # Plus sign
        }

        db.single_insert(test_db, row, "users")

        # Verify data integrity
        rows = db.select(test_db, None, {"user_id": "U001"}, None, "users")
        assert rows[0]["USERNAME"] == "alice's account"
        assert rows[0]["EMAIL"] == "alice+test@example.com"

    def test_null_values(self, test_db, test_table_spec):
        """Test handling of NULL values"""
        db.create_table(test_db, test_table_spec, "users")

        row = {
            "user_id": "U001",
            "username": "alice",
            # email and age intentionally omitted (will be NULL)
        }

        db.single_insert(test_db, row, "users")

        rows = db.select(test_db, None, {"user_id": "U001"}, None, "users")
        assert rows[0]["EMAIL"] is None
        assert rows[0]["AGE"] is None

    def test_empty_table_operations(self, test_db, test_table_spec):
        """Test operations on empty table"""
        db.create_table(test_db, test_table_spec, "users")

        # Select from empty table
        rows = db.select(test_db, None, None, None, "users")
        assert len(rows) == 0

        # Update on empty table
        affected = db.update(test_db, {"age": 30}, None, "users")
        assert affected == 0

        # Delete from empty table
        deleted = db.delete(test_db, None, "users")
        assert deleted == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
