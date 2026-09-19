"""Run: python examples/01_runnables.py"""
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser

normalize = RunnableLambda(lambda text: text.strip().lower())
make_message = RunnableLambda(lambda text: AIMessage(content=f"You asked: {text}"))
chain = normalize | make_message | StrOutputParser()
print(normalize.invoke("  API Tests  "))
print(chain.invoke("  API Tests  "))
