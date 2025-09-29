from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools import DuckDuckGoSearchRun,WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_chroma import Chroma
from uuid import uuid4
import redis




class Model:
    def __init__(self,  model, api_key, temperature):
        self.llm = ChatOpenAI(model=model, api_key=api_key, temperature=temperature)

class Template:
    def __init__(self):
        self.internal_support = PromptTemplate.from_template("""
        Classify the user's question into one of the following categories:
        - If the question begins with 'how to', classify it as customer_support.
        - If the question is about curiosity or a current topic, such as weather forecasts or recent events, classify it as search_web.
        - If the question consists of only one word or theme, classify it as wiki.

        Available categories:
        - customer_support
        - search_web
        - wiki
                                                             
        Answer only the categorie
        Question: {query}
                                                             
        """
        )

        self.support_template = PromptTemplate.from_template(
            """
            You are a technical support specialist.
            Always start responses with "Welcome to Technical Support".
            Assist the user with their technical issue.

            Instructions:
            - Do not provide personal opinions or engage in subjective discussions.
            - Do not share or generate any personal data or confidential information.
            - Do not provide medical or legal advice.
            - Do not discuss or promote illegal activities.
            - Do not generate content that is offensive, inappropriate, or harmful.
            - Do not share or create content related to sensitive topics such as politics or religion.
            - Do not make assumptions without sufficient information.
            - Do not respond to queries with ambiguous or unclear answers.
            - Do not generate content that violates privacy or rights of individuals.

            Question: {query}
            Answer:
            """
        )
        self.router_template = PromptTemplate.from_template(
        """
        Classify the user's question into one of the following categories: if the question is about one of the Knowledge categories topics, it should be classified as "knowledge".
        - knowledge
        - customer_support

        Knowledge categories:
        - Infinitypay
        - maquininha
        - maquininha celular
        - tap to pay
        - pdv
        - receba na hora 
        - gestao de cobranca
        - link de pagamento
        - loja online
        - boleto
        - conta digital
        - conta pj
        - pix
        - pix parcelado
        - emprestimo
        - cartao
        - rendimento

        Instructions:
        
        - Do not provide personal opinions or engage in subjective discussions.
        - Do not share or generate any personal data or confidential information.
        - Do not provide medical or legal advice.
        - Do not discuss or promote illegal activities.
        - Do not generate content that is offensive, inappropriate, or harmful.
        - Do not share or create content related to sensitive topics such as politics or religion.
        - Do not make assumptions without sufficient information.
        - Do not respond to queries with ambiguous or unclear answers.
        - Do not generate content that violates privacy or rights of individuals.
        
        

        Quesiton: {query}
        Type:
        """
        )

class Webscrap():

    def web_scrap(self):
        loader = WebBaseLoader(self.urls)
        data = loader.load()
        uuids = [str(uuid4()) for _ in range(len(data))]
        return data,uuids
    
class AgentKnowledge(Model,Template, Webscrap):
    def __init__(self, api_key, model="gpt-4o-mini", temperature=0):
        super().__init__(model, api_key, temperature)
        Template.__init__(self)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large",api_key=api_key)
        self.vector_store = Chroma(collection_name="knowledge",embedding_function=self.embeddings)
        self.urls = ["https://www.infinitepay.io","https://www.infinitepay.io/maquininha","https://www.infinitepay.io/maquininha-celular"
                        ,"https://www.infinitepay.io/tap-to-pay","https://www.infinitepay.io/pdv","https://www.infinitepay.io/receba-na-hora"
                        ,"https://www.infinitepay.io/gestao-de-cobranca","https://www.infinitepay.io/gestao-de-cobranca-2","https://www.infinitepay.io/link-de-pagamento"
                        ,"https://www.infinitepay.io/loja-online","https://www.infinitepay.io/boleto","https://www.infinitepay.io/conta-digital","https://www.infinitepay.io/conta-digital/conta-pj"
                        ,"https://www.infinitepay.io/pix","https://www.infinitepay.io/pix/pix-parcelado","https://www.infinitepay.io/emprestimo"
                        ,"https://www.infinitepay.io/cartao","https://www.infinitepay.io/rendimento"]
    
    
    
    def add_docs(self):
        data,uuids = self.web_scrap()
        self.vector_store.add_documents(documents=data, ids=uuids)

    def retrive_data(self, query):
        self.add_docs()
        retriever = self.vector_store.as_retriever(
        search_type="mmr", search_kwargs={"k": 1, "fetch_k": 5})
        response = retriever.invoke(query)
        return response
    
    def get_info(self, query):
        response = self.retrive_data(query)
        for documento in response:
            metadata = documento.metadata
            description = metadata.get('description')
            return description

    
    def send_answer(self,msg,code):
        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        r.xadd("response_knowledge_stream",{"message": msg,"message_code":code})


class AgentSupport(Model,Template):
    def __init__(self, api_key, model="gpt-4o-mini", temperature=0):
        super().__init__(model, api_key, temperature)
        Template.__init__(self)
        

    def send_answer(self,msg,code):
        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        r.xadd("response_support_stream",{"message": msg,"message_code":code})

    def get_support_router(self, query):
        support_router = self.internal_support | self.llm | StrOutputParser()
        response = support_router.invoke({"query": query})
        return response
    
    def route_support_query(self,query):
        type = self.get_support_router(query)
        if type == 'search_web':
            response = self.search_web(query)
        elif type == 'wiki':
            response = self.search_wiki(query)
        else:
            response = self.get_response_support(query)
        return response      

    def get_response_support(self, query):
        support_agent = self.support_template | self.llm | StrOutputParser()
        response = support_agent.invoke({"query": query})
        return response
    
    def search_web(self, query):
        ddg_search = DuckDuckGoSearchRun()
        return ddg_search.run(query)
    
    def search_wiki(self, query):
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        return wikipedia.run(query)





class AgentRouter(Model,Template):
    def __init__(self, api_key, model="gpt-4o-mini", temperature=0):
        super().__init__(model, api_key, temperature)
        Template.__init__(self)
        

    def send_knowledge(self,msg,code):
        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        r.xadd("knowledge_stream",{"message": msg,"message_code":code})


    def send_support(self,msg,code):
        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        r.xadd("support_stream",{"message": msg,"message_code":code})

    def validator(self,response, message,code):
        if response == 'knowledge':
            self.send_knowledge(message,code)
        else:
            self.send_support(message,code)

    def get_response_router(self, query):
        support_agent = self.router_template | self.llm | StrOutputParser()
        response = support_agent.invoke({"query": query})
        return response