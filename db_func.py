"""
Contains all the CRUD functions of a db + table.
"""

import sqlite3


def create_database(name: str):
    conn = sqlite3.connect(f"{name}.db")
    conn.row_factory = sqlite3.Row
    return conn


def connect_database(path: str):
    conn = sqlite3.connect(f"{path}")
    conn.row_factory = sqlite3.Row
    return conn


"""
spec: dictionary: column_name : [datatype, specifiers]. + Primary Key : column_name + Foreign Key : [(column name,ref_table)]

any column with primary key will automatically have the NOT NULL , UNIQUE charecteristic added to it.

returns -1 if primary_key->column_name doesnt exist in the keys, similarly for foreign keys.

returns -2 for all other sql-related errors (mismatched texts , what not.

https://www.w3schools.com/sql/sql_datatypes.asp -> refer for a list of datatypes.

If we have a datatype(arg) .. make sure to add in the args too.

all column names are automatically uppercased (handled inside the functions)
"""


def create_table(conn, spec, name):
    f_string = ""
    for col, type_list in spec.items():
        if col == "Primary Key" or col == "Foreign Key":
            continue

        f_string += col.upper() + " " + type_list[0].upper() + " "
        if "Primary Key" in spec and spec["Primary Key"] == col:
            f_string += "NOT NULL UNIQUE PRIMARY KEY,\n"
        elif len(type_list) > 1:
            f_string += type_list[1] + ",\n"
        else:
            f_string += ",\n"

    if "Foreign Key" in spec:
        for col, ref in spec["Foreign Key"]:
            f_string += (
                "FOREIGN KEY ("
                + col.upper()
                + ") REFERENCES "
                + ref.upper()
                + "("
                + col.upper()
                + "),\n"
            )

    f_string = f_string[:-2] + "\n"

    cursor = conn.cursor()
    query = "CREATE TABLE " + name.upper() + "(" + f_string + ");"
    cursor.execute(query)
    cursor.close()
    return


def drop_table(conn, name):
    query = "DROP TABLE IF EXISTS " + name.upper()
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()
    return


"""
Insert (by value) -> dictionary based insert.
"""


def single_insert(conn, cmd_dict, name):
    col_str = ""
    val_str = ""
    val_list = []

    for col, val in cmd_dict.items():
        col_str += col.upper() + " ,"
        val_str += "?,"
        val_list.append(val)

    col_str = col_str[:-1]
    val_str = val_str[:-1]

    query = "INSERT INTO " + name.upper() + " (" + col_str + ") VALUES (" + val_str + ");"
    cursor = conn.cursor()
    cursor.execute(query, tuple(val_list))
    conn.commit()
    cursor.close()
    return


"""
Select query -> for now we allow where + orderby commands.
"""


def select(conn, col_list, where_clause, order_by, name):
    q = "SELECT "
    if col_list is None or len(col_list) == 0:
        q += "*"
    else:
        for c in col_list:
            q += c.upper() + ","
        q = q[:-1]

    q += " FROM " + name.upper()

    vals = []
    if where_clause is not None:
        if isinstance(where_clause, dict):
            q += " WHERE "
            for k, v in where_clause.items():
                q += k.upper() + " = ? AND "
                vals.append(v)
            q = q[:-5]
        else:
            q += " WHERE " + where_clause

    if order_by is not None:
        q += " ORDER BY "
        if isinstance(order_by, list):
            for c in order_by:
                q += c.upper() + ","
            q = q[:-1]
        else:
            q += order_by.upper()

    q += ";"

    cursor = conn.cursor()
    if len(vals) > 0:
        cursor.execute(q, tuple(vals))
    else:
        cursor.execute(q)
    rows = cursor.fetchall()
    cursor.close()
    return rows


"""
Update rows -> where claus allowed
"""


def update(conn, col_list, where_clause, name):
    q = "UPDATE " + name.upper() + " SET "
    vals = []

    for k, v in col_list.items():
        q += k.upper() + " = ?,"
        vals.append(v)
    q = q[:-1]

    if where_clause is not None:
        if isinstance(where_clause, dict):
            q += " WHERE "
            for k, v in where_clause.items():
                q += k.upper() + " = ? AND "
                vals.append(v)
            q = q[:-5]
        else:
            q += " WHERE " + where_clause

    q += ";"

    cursor = conn.cursor()
    cursor.execute(q, tuple(vals))
    conn.commit()
    rc = cursor.rowcount
    cursor.close()
    return rc


"""
Delete rows ->
"""


def delete(conn, cmd_dict, name):
    q = "DELETE FROM " + name.upper()
    vals = []

    if cmd_dict is not None:
        if isinstance(cmd_dict, dict):
            q += " WHERE "
            for k, v in cmd_dict.items():
                q += k.upper() + " = ? AND "
                vals.append(v)
            q = q[:-5]
        else:
            q += " WHERE " + cmd_dict

    q += ";"

    cursor = conn.cursor()
    if len(vals) > 0:
        cursor.execute(q, tuple(vals))
    else:
        cursor.execute(q)
    conn.commit()
    rc = cursor.rowcount
    cursor.close()
    return rc
