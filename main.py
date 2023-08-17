import chainlit as cl
# from chainlit import AskUserMessage, Message
from chainlit import user_session

from src.loader import init_vector_db, load_data
from src.model import qa_bot
from src.utils import load_config

cfg = load_config()

init_vector_db()


@cl.action_callback("Rebuild Vector DB")
async def on_action(action):
    response = load_data()
    await cl.Message(content=f"{response}").send()
    # Optionally remove the action button from the chatbot user interface
    await action.remove()


## Cgainlit ##
@cl.on_chat_start
async def start():
    user_session.set("is_result_from_llm", False)
    # Sending an action button within a chatbot message
    actions = [
        cl.Action(
            name="Rebuild Vector DB",
            value=True,
            description="Run this if you have uploaded new data",
        )
    ]

    chain = qa_bot()
    msg = cl.Message(
        content="Hello there! 😊 How can I assist you today? Feel free to let me know!",
        actions=actions,
    )
    await msg.send()

    # Option 1 :
    # msg = cl.Message(content = "Want to rebuild vectorDb!", actions=actions)
    # await msg.send()

    # Option 2 : Take yes  or No
    # res = await AskUserMessage(content="Want to rebuild vectorDb! y or n", timeout=30 ).send()
    # if res:
    #     print(res)
    #     await Message(
    #         content=f"Your selected : {res['content']}.\n We will rebuild vectorDB!",
    #     ).send()

    cl.user_session.set("chain", chain)


@cl.on_message
async def main(message):
    chain = cl.user_session.get("chain")

    res = await chain.acall(message)
    answer = res["result"]
    # sources = res["source_documents"]

    is_result_from_llm = user_session.get("is_result_from_llm")
    if not is_result_from_llm:
        # I have added this code here because of the hacky StreamingStdOutCallbackHandler. When a user enters the same query they have searched before, the result comes from the chainlit database and no large language model (LLM) is used, so no token code runs and hence no new result is generated. Therefore, we simply return the result from the history. However, when the LLM runs, we don't want to return duplicate results as it would be redundant.
        await cl.Message(content=answer).send()
       
    user_session.set("is_result_from_llm", False)
