from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from utils.llm_engine import AgentKnowledge
from utils.config import api_key
import redis

agent = AgentKnowledge(api_key)

r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

last_id = "0"  

while True:
    messages = r.xread({"knowledge_stream": last_id}, block=5000, count=10)
    if messages:
        for stream_name, msgs in messages:
            for message_id, message_data in msgs:
                question = message_data["message"]
                code = message_data["message_code"]
                rag_response = agent.get_info(question)
                agent.send_answer(rag_response,code)
                last_id = message_id



