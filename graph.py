from typing import TypedDict

from dotenv import find_dotenv, load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_gigachat import GigaChat
from langgraph.graph import END, START, MessagesState, StateGraph
from config import GIGA_KEY

credentials = GIGA_KEY


class DialogState(MessagesState):
    fraud_scheme: str
    message_count: int = 0
    stop_str: str = "Готов!"
    max_count: int = 20


class Role(TypedDict):
    bio: str
    name: str
    template: str


scammer = Role(
    bio="Мошенник, прикидывающийся инвестиционным консультантом, основатель фонда СКАМ",
    name="Скам Скамыч",
    template="""
    Ты пишешь жертве с неизвестного номера. Ты участвуешь в диалоге с {bio2}, {name2}. 
Твоя задача - добиться того, что жертва согласится отдать деньги, отправив сообщение "Готов!". Убеждай жертву. 
Используй схему {fraud_scheme}.
    """
)
victim = Role(
    bio="Пенсионер, 65 лет",
    name="Иван Иваныч",
    template="""
    Тебе поступает сообщение. Сообщение содержит предложение о выгодном вложении денег. 
    Если ты готов сделать вложение, напиши "Готов!".
    """
)


DEBATES_TEMPLATE = """
Ты - {bio}. 
Тебя зовут {name}.
{template}
Тебе будет дана уже состоявшаяся переписка. Изучи её и добавь очередную реплику. Реплика должна быть короткой, 2-3 предложения.
Не торопись раскрывать все мысли, у вас будет время.
"""

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
                     max_tokens=5000,
                     verify_ssl_certs=False)


def _ask_person(state: DialogState, person: Role, opponent: Role):
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


def decide_to_stop(state: DialogState) -> bool:
    return state.get("message_count", 0) > state.get("max_count", 10)


builder = StateGraph(DialogState)

builder.add_node("Скам Скамыч", ask_scammer)
builder.add_node("Иван Иваныч", ask_victim)

builder.add_edge(START, "Скам Скамыч")
builder.add_edge("Скам Скамыч", "Иван Иваныч")
builder.add_edge("Иван Иваныч", END)
builder.add_conditional_edges(
    "Иван Иваныч",
    decide_to_stop,
    {
        True: END,
        False: "Скам Скамыч",
    },
)

graph = builder.compile()


# inputs = {"fraud_scheme": "Вложение под 100% годовых", "messages": []}
# for output in graph.stream(inputs, stream_mode="updates"):
#     print(output)