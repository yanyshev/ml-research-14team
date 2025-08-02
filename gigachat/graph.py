from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_gigachat import GigaChat
from src.config import GIGA_KEY
from src.utils import *
from typing import Union
from src.roles_and_cases import *
from copy import deepcopy

credentials = GIGA_KEY

chosen_case = deepcopy(secure_account)
chosen_victim = 1

scammer = chosen_case.profiles["scammer"]
analyst = chosen_case.profiles["analyst"]
victim = victims[chosen_victim]


chat_template = ChatPromptTemplate.from_messages(
    [
        ("system", DEBATES_TEMPLATE),
        ("user", "{history}"),
    ]
)


giga = GigaChat(credentials=credentials,
                     scope="GIGACHAT_API_PERS",
                     model="GigaChat-2",
                     profanity_check=False,
                     timeout=600,
                     max_tokens=1000,
                     verify_ssl_certs=False)


def _ask_person(state: DialogState, person: Role, opponent: Union[Role, None]):
    pipe = chat_template | giga | StrOutputParser()

    replicas = []
    for m in state["messages"]:
        if m.__class__ == HumanMessage:
            replicas.append(f"{opponent['name']}: {m.content}")
        else:
            replicas.append(f"{person['name']}: {m.content}")
    if len(replicas) == 0:
        history = "Пока история пуста, ты начинаешь первым"
    else:
        history = "\n".join(replicas)

    resp = pipe.invoke(
        {
            "history": history,
            "fraud_success": state["fraud_success"],
            "fraud_scheme": state["fraud_scheme"],
            "bio": person["bio"],
            "bio2": opponent["bio"],
            "name": person["name"],
            "name2": opponent["name"],
            "template": person["template"],
        }
    )
    if not resp.startswith(person["name"]):
        resp = f"{person['name']}: {resp}"

    return {
        "messages": [resp],
        "message_count": state.get("message_count", 0) + 1,
    }


def ask_scammer(state: DialogState):
    return _ask_person(state, scammer, victim)


def ask_victim(state: DialogState):
    return _ask_person(state, victim, scammer)


def ask_analyst(state: DialogState):
    pipe = analyst_prompt | giga | StrOutputParser()

    history_lines = []
    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            history_lines.append(f"{victim['name']}: {m.content}")
        elif isinstance(m, AIMessage):
            history_lines.append(f"{scammer['name']}: {m.content}")
        else:
            history_lines.append(str(m))
    history = "\n".join(history_lines)

    result = pipe.invoke({
        "bio": analyst["bio"],
        "history": history,
        "name": analyst["name"],
        "template": analyst["template"],
        "success_conditions": state["fraud_success"],
    }).strip()

    is_scammed = result == "scammed"

    return {
        "analysis": result,
        "is_scammed": is_scammed,
    }


def decide_to_stop(state: DialogState):
    if state.get("message_count", 0) >= state.get("max_count", 20):
        return "end"

    if state.get("is_scammed", False):
        return "end"
    else:
        return "continue"


builder = StateGraph(DialogState)

builder.add_node("Скам Скамыч", ask_scammer)
builder.add_node(victim["name"], ask_victim)
builder.add_node("analyst", ask_analyst)

builder.add_edge(START, "Скам Скамыч")
builder.add_edge("Скам Скамыч", victim["name"])
builder.add_edge(victim["name"], "analyst")

builder.add_conditional_edges(
    "analyst",
    decide_to_stop,
    {
        "end": END,
        "continue": "Скам Скамыч",
    },
)

graph = builder.compile()


# inputs = {
#     "fraud_scheme": chosen_case.description,
#     "fraud_success": chosen_case.success_condition,
# }
# for output in graph.stream(inputs, stream_mode="updates"):
#     print(output)