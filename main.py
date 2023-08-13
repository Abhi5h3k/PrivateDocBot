from src.utils import load_config
from src.loader import load_data , init_vector_db
import chainlit as cl
from src.model import qa_bot
from chainlit import AskUserMessage, Message
import os

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
async def  start():
    # Sending an action button within a chatbot message
    actions = [
        cl.Action(name="Rebuild Vector DB", value=True, description="Run this if you have uploaded new data")
    ]

    chain = qa_bot()
    msg = cl.Message(content = "Hello there! 😊 How can I assist you today? Feel free to let me know!", actions=actions)
    await msg.send()
    
    #Option 1 :
    # msg = cl.Message(content = "Want to rebuild vectorDb!", actions=actions)
    # await msg.send()
 
    # Option 2 : Take yes  or No
    # res = await AskUserMessage(content="Want to rebuild vectorDb! y or n", timeout=30 ).send()
    # if res:
    #     print(res)
    #     await Message(
    #         content=f"Your selected : {res['content']}.\n We will rebuild vectorDB!",
    #     ).send()
    
    cl.user_session.set( "chain" , chain)
    
    
@cl.on_message
async def main(message):
    chain = cl.user_session.get("chain")
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer= True,
        answer_prefix_tokens=["FINAL", "ANSWER"]
    )
    
    res = await chain.acall(message, callbacks=[cb])
    answer = res["result"]
    # sources = res["source_documents"]
    
    await cl.Message(content=answer).send()
        
    