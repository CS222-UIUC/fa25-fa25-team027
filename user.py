from typing import List
from meeting_record import MeetingRecord
import class_helpers
import db_func


class User:
    user_id:str
    username:str
    meetings: List[MeetingRecord]
    last_meeting_id:int

    def __init__(self,conn,username):
        if(check_username(conn,username)):
            uid = 0 
            mid = 0
            self.last_meeting_id = mid
            meetings = []
            queries = fetch_user_meetings(conn,username)
            for query in queries:
                meeting_stat = dict(query) 
                uid = meeting_stat["user_id"]
                mid = meeting_stat["meeting_id"]
                if(mid > self.last_meeting_id):
                    self.last_meeting_id = mid
                meetings.append(MeetingRecord(meeting_stat))
            
            self.user_id = uid
            self.meetings = meetings
            self.username = username
        else:
            '''
            DOES NOT INSERT INTO TABLE ->  ONLY INSERTS WHEN LEN(MEETINGS) > 0
            '''
            self.user_id = fetch_last_user_id(conn,username)
            self.username = username
            self.meetings = []
            self.last_meeting_id = 0

    '''
    A user can only add a meeting through transcription -> hence ollama_input is always true.
    '''
    def add_meeting(self,conn,ollama_input):
        new_meeting = MeetingRecord(ollama_input,True)
        new_meeting.set_field("meeting_id",last_meeting_id)
        self.last_meeting_id += 1
        (self.meetings).append(new_meeting)
        insert_dict = new_meeting.format_for_insert()
        insert_dict["username"] = self.username
        insert_dict["user_id"] = self.user_id
        insert_meeting(conn,insert_dict)
        

    '''
    drops the meeting entry and updates the meetings list.
    '''
    def remove_meeting(self,conn,meeting_index):
        meeting = (self.meetings).pop(meeting_index)
        meeting_dict = meeting.format_for_insert()
        meeting_dict["username"] = self.username
        meeting_dict["user_id"] = self.user_id
        drop_meeting(conn,meeting_dict)

    '''
    Very dependent on DOM -> assumes that the names of the tags in the input fields in the front_end is the same. 
    But for now if a user makes a change in key_points in meeting i -> i is the position of the meeting in self.meetings
    the following are the formats for field:
    if we have a edit on summary_heading / meeting_date -> field = ("summary_heading") / ("meeting_date")
    if we have a edit on key_points at point i -> field = ("key_points",i)
    if we have a edit on the i'th action_item at field k (either task, assignee, deadline) -> field = ("action_items",i,k)
    '''

    def update_meeting(self,conn,meeting_index,field,change):
        meeting = (self.meetings)[meeting_index]
        m_value = meeting.get_field(field[0])
        if(len(field) == 1):
            m_value = change
        elif(len(field) == 2):
            m_value[field[1]] = change
        elif(len(field) == 3):
            m_value[field[1]][field[2]] = change
        meeting.set_field(field[0],m_value)
        (self.meetings)[meeting_index] = meeting
        update_meeting(conn,self.user_id,self.username,meeting)

    
    '''
    Removes all records of the user in the table -> and set all fields to the default 0.
    '''
    def delete_user(self,conn):
        delete(conn,{"user_id":self.user_id,"username":username},"MEETINGS_TABLE")
        self.user_id = 0
        self.username = ""
        self.meetings = []

