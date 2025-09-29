# main.py
from fastapi import FastAPI
import routes.api_routes as ar
import uvicorn
import redis
import json

app = FastAPI(
    title='Agents API',
    version='0.0.1',
    description='AI Agents with FastAPI'
)


app.include_router(ar.router, tags=['agents'])


if __name__ == '__main__':
  
    uvicorn.run("main:app", host="0.0.0.0", port=8000)