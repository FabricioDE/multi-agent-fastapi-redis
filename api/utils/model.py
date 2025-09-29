from pydantic import BaseModel




class MessagePost(BaseModel):
    message: str
    user_id: str

class ResponsePost(BaseModel):
    message: str
    message_code: str