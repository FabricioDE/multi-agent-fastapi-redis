from utils.llm_engine import AgentRouter
from utils.config import api_key
import redis


r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
agent = AgentRouter(api_key)


last_id = "0"  


while True:
    messages = r.xread({"router_stream": last_id}, block=5000, count=10)
    if messages:
        print('new message')
        for stream_name, msgs in messages:
            for message_id, message_data in msgs:
                question = message_data["message"]
                code = message_data["message_code"]
                response = agent.get_response_router(question)
                agent.validator(response, question, code)
                
                last_id = message_id




