from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from utils.llm_engine import AgentSupport
from utils.config import api_key
import redis


r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
agent = AgentSupport(api_key)

last_id = "0"  

while True:
    messages = r.xread({"support_stream": last_id}, block=5000, count=10)
    if messages:
        for stream_name, msgs in messages:
            for message_id, message_data in msgs:
                question = message_data["message"]
                code = message_data["message_code"]
                response = agent.route_support_query(question)
                agent.send_answer(response,code)
                last_id = message_id
