'''
This is the object that the database queries will return -> follows the frontend description of a meeting record.

Add all manipulation or helper functions in the file.

TABLE SCHEMA:
    user_id:
    username:
    meeting_id:
    meeting_date:
    summary_heading:
    key_points:
    action_items:
'''

from datetime import datetime
import json

class MeetingRecord:

    def __init__(self,meeting_stats,ollama = False):
        if(ollama == True):
            self.meeting_id = 0
            self.meeting_date = datetime.today().strftime('%Y-%m-%d')
            self.summary_heading = meeting_stats["summary_heading"] 
            self.key_points = meeting_stats["key_points"]
            self.action_items = meeting_stats["action_items"]
        else:
            self.meeting_id = json.loads(meeting_stats["meeting_id"])
            self.meeting_date = json.loads(meeting_stats["meeting_date"])
            self.summary_heading = json.loads(meeting_stats["summary_heading"])
            self.key_points = json.loads(meeting_stats["key_points"])
            self.action_items = json.loads(meeting_stats["action_items"])

    def get_field(self,field):
        return getattr(self,field,None)


    def set_field(self,field,value):
        setattr(self,field,value)

    def format_for_insert(self):
        attr_dict = self.__dict__
        output_dict = {}
        for(k,v) in attr_dict.items():
            output_dict[k] = json.dumps(v)
        return output_dict

