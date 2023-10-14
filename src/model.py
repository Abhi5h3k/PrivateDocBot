from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

import chainlit as cl
from chainlit import user_session
from langchain import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import CTransformers
from langchain.schema.output import LLMResult
from langchain.vectorstores import FAISS

from src.prompts import qa_template1
from src.utils import determine_threads_to_use, load_config

cfg = load_config()


# <- HuggingFaceEmbeddings
def get_sentence_transformer():
    model_folder_path = "models/sentence-transformers/all-MiniLM-L6-v2"
    # This will download the model to the given path and use it from there.
    return HuggingFaceEmbeddings(cache_folder=model_folder_path)


# ->

# <- Main llm


def set_custom_prompt():
    """
    Prompt template for QA retrieval for each vectorstore
    """
    prompt = PromptTemplate(
        template=qa_template1, input_variables=["context", "question"]
    )
    return prompt


# As of now, I haven't discovered a straightforward solution to achieve this due to the lack of helpful documentation and time constraints. Thus, I've implemented a somewhat hacky method to stream tokens to the UI. I'm uncertain if this approach is technically correct, but it does accomplish the task at hand. According to the documentation, this functionality should work seamlessly, but regrettably, I've encountered issues in its implementation. Please feel free to make any necessary changes to rectify and improve the implementation.
class StreamingStdOutCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming. Only works with LLMs that support streaming."""

    def __init__(self):
        self.logtxt = ""
        self.msg = cl.Message(content="")

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM starts running."""
        user_session.set("is_result_from_llm", True)

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""

        await self.msg.send()
        self.logtxt += token

        self.msg.content = self.logtxt
        await self.msg.update()

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        self.logtxt = ""
        self.msg = cl.Message(content="")
        # user_session.set("is_result_from_llm", False)


def build_llm(model):
    # Call the function to get the number of threads to use
    num_threads = determine_threads_to_use()
    print(f"Number of Threads avaialble : {num_threads}")

    # Local CTransformers model
    llm = CTransformers(
        model=cfg.MODEL_BIN_DIR + "/" + model,
        model_type="llama",
        config={
            "max_new_tokens": cfg.MAX_NEW_TOKENS,
            "temperature": cfg.TEMPERATURE,
            "threads": num_threads,
            "stream": True,
            "repetition_penalty": 1.3,
        },
        callbacks=[StreamingStdOutCallbackHandler()],
    )

    return llm


def build_retrieval_qa(llm, qa_prompt, vectordb):
    # Question
    # {'k': cfg.VECTOR_COUNT} how many search to return

    # stuff document : It takes a list of documents, inserts them all into a prompt and passes that prompt to an LLM.
    # https://python.langchain.com/docs/modules/chains/document/stuff

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(search_kwargs={"k": cfg.VECTOR_COUNT}),
        return_source_documents=cfg.RETURN_SOURCE_DOCUMENTS,
        chain_type_kwargs={"prompt": qa_prompt},
    )
    return qa_chain


def qa_bot(selected_model_name="mistral-7b-openorca.Q4_K_M.gguf"):
    # setup QA Bot

    embeddings = get_sentence_transformer()
    vectordb = FAISS.load_local(cfg.DB_FAISS_PATH, embeddings)

    llm = build_llm(selected_model_name)
    qa_prompt = set_custom_prompt()

    qa_bot = build_retrieval_qa(llm, qa_prompt, vectordb)

    return qa_bot


# ->
