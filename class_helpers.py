import db_func
from typing import List
from meeting_record import MeetingRecord

'''
NAME: MEETINGS_TABLE

TABLE_SCHEMA: 
    user_id:
    username:
    meeting_id:
    meeting_date:
    summary_heading:
    key_points:
    action_items: (string of lists[dicts] -> SCHEMA : {"assignee","task","deadline","status"})
'''


MAIN_TABLE = "MEETINGS_TABLE"  


def check_username(conn,username):
    query = select(conn,["DISTINCT user_id"],{"username":username},None,MAIN_TABLE)
    if(len(query) == 1):
        return True
    else:
        return False


'''
Assumes that username doesnt exist in the table. -> returns a user_id + username.
Note we create a dummy user_id , username entry -> that must be deleted iff the user doesnt input any meetings to transcribe for version 1.
'''

def fetch_last_user_id(conn,username):
    query = list(select(conn,["MAX(user_id)"],None,None,MAIN_TABLE))
    user_id = 0
    if(len(query) > 0):
        user_id = int(list(query[0])) + 1
    return user_id


def delete_user(conn,user_id,username):
    delete(conn, {"user_id": user_id, "username":username},MAIN_TABLE)
    return


def fetch_user_meetings(conn,username):
    query = select(conn,[],{"username":username},["meeting_id"],MAIN_TABLE)
    return query


def insert_meeting(conn,insert_dict):
    single_insert(conn,insert_dict,MAIN_TABLE)


def drop_meeting(conn,drop_dict):
    delete(conn,drop_dict,MAIN_TABLE) 
    return

def update_meeting(conn,user_id,username,meeting):
    meeting_id = meeting.format_for_insert()["meeting_id"]
    cond_dict = {"user_id": user_id, "username": username, "meeting_id": meeting_id}
    update(conn,meeting.format_for_insert(),cond_dict,MAIN_TABLE)
    return


