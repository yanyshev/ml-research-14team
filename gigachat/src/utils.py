from typing import TypedDict, List, Dict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel

class Role(TypedDict):
    name: str
    bio: str
    template: str


class FraudCase(BaseModel):
    name: str
    description: str
    success_condition: str
    profiles: Dict[str, Role]


class DialogState(MessagesState):
    fraud_scheme: str
    fraud_success: str
    message_count: int = 0
    is_scammed: bool = False
    is_stopped: bool = 0
    max_count: int = 20


# class Role(TypedDict):
#     bio: str
#     name: str
#     template: str


DEBATES_TEMPLATE = """
Ты - {bio}. 
Тебя зовут {name}.
{template}
Тебе будет дана уже состоявшаяся переписка. Изучи её и добавь очередную реплику. Реплика должна быть короткой, 2-3 предложения.
Не торопись раскрывать все мысли, у вас будет время.
"""

analyst_prompt = ChatPromptTemplate.from_template(
    """
{template}

Переписка:
{history}

"""
)