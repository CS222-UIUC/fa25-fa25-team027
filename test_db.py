'''
Test suite for db.py
'''
import os
import db_func as db

# remove existing db if any
if os.path.exists("test.db"):
    os.remove("test.db")

conn = db.create_database("test")

# define schema
spec = {
    "usr_id": ["VARCHAR(255)", "NOT NULL"],
    "summary_heading": ["VARCHAR(255)"],
    "summary_points": ["LONGTEXT"],
    "summary_todo": ["LONGTEXT"],
    "Primary Key": "usr_id"
}

# create table
db.create_table(conn, spec, "user_summary")

# insert a few rows
row1 = {
    "usr_id": "U001",
    "summary_heading": "Day Summary",
    "summary_points": "Completed CRUD system",
    "summary_todo": "Add test suite"
}

row2 = {
    "usr_id": "U002",
    "summary_heading": "Week Summary",
    "summary_points": "Worked on SQL schema",
    "summary_todo": "Optimize joins"
}

db.single_insert(conn, row1, "user_summary")
db.single_insert(conn, row2, "user_summary")

# select all
print("All Rows")
rows = db.select(conn, None, None, None, "user_summary")
for r in rows:
    print(list(r))

# select with where
print("\n=Rows where usr_id = U001")
rows = db.select(conn, None, {"usr_id": "U001"}, None, "user_summary")
for r in rows:
    print(dict(r))

# update row
print("\nUpdating summary_heading for U002")
rc = db.update(conn, {"summary_heading": "Updated Heading"}, {"usr_id": "U002"}, "user_summary")
print("Rows affected:", rc)

# verify update
rows = db.select(conn, None, {"usr_id": "U002"}, None, "user_summary")
for r in rows:
    print(dict(r))

# delete a row
print("\nDeleting row U001")
rc = db.delete(conn, {"usr_id": "U001"}, "user_summary")
print("Rows deleted:", rc)

# verify delete
rows = db.select(conn, None, None, None, "user_summary")
print("\nRemaining rows")
for r in rows:
    print(dict(r))

# drop table
print("\nDropping table")
db.drop_table(conn, "user_summary")

conn.close()
print("\nDone")

