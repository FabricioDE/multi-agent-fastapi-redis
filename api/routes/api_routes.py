from utils.model import MessagePost, ResponsePost
from fastapi import APIRouter, HTTPException, status,Response
import redis
import json
import asyncio
import random

router = APIRouter()
r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)



class APIPost():
    def __init__(self):
        self.last_id_support = "0"  
        self.last_id_knowledge = "0"  

    def generate_code(self):
        return random.randint(10000, 99999)

    def process_response(self,response):
        for stream_name, msgs in response:
            for message_id, message_data in msgs:
                message = message_data["message"]
                code = message_data["message_code"]
        return message, code, message_id
                

    async def get_result(self):        
        await asyncio.sleep(3)
        response_support = r.xread({"response_support_stream": self.last_id_support}, block=5000, count=10)
        response_knowledge = r.xread({"response_knowledge_stream": self.last_id_knowledge}, block=5000, count=10)

        if response_support:
            message, code, message_id = self.process_response(response_support)
            self.last_id_support = message_id
        
        if response_knowledge:
            message, code, message_id = self.process_response(response_knowledge)
            self.last_id_knowledge = message_id
    
        return message, code


post = APIPost()

@router.post("/api/v1/agent", status_code= status.HTTP_201_CREATED,
             summary='Post Endpoint', description='Post Agents Request', response_model=ResponsePost)
async def receive_message(request: MessagePost):
    
    code_send = post.generate_code()
    r.xadd("router_stream",{"message": request.message,"user_id": request.user_id,"message_code": code_send})
    result = {}
    response, code_return = await post.get_result()
    result['message'] = response
    result['message_code'] = code_return
    return result
    