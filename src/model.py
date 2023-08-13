from src.utils import load_config, determine_threads_to_use
from langchain.embeddings import HuggingFaceEmbeddings
from src.prompts import qa_template1
from langchain import PromptTemplate
from langchain.llms import CTransformers
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS

cfg = load_config()

#<- HuggingFaceEmbeddings
def get_sentence_transformer():
    model_folder_path = 'models/sentence-transformers/all-MiniLM-L6-v2'
    # This will download the model to the given path and use it from there.
    return HuggingFaceEmbeddings(cache_folder =model_folder_path)

# ->

# <- Main llm

def set_custom_prompt():
    """
    Prompt template for QA retrieval for each vectorstore
    """
    prompt = PromptTemplate(template=qa_template1,
                            input_variables=['context', 'question'])
    return prompt

def build_llm(model):
    # Call the function to get the number of threads to use
    num_threads = determine_threads_to_use()
    print(f'Number of Threads avaialble : {num_threads}')
    
    # Local CTransformers model
    llm = CTransformers(model=cfg.MODEL_BIN_DIR+"/"+model,
                        model_type='llama',
                        config={'max_new_tokens': cfg.MAX_NEW_TOKENS,
                                'temperature': cfg.TEMPERATURE,
                                'threads': num_threads,
                                'stream' : True
                                }
                        )

    return llm

def build_retrieval_qa(llm, qa_prompt, vectordb): 
    #Question    
    # {'k': cfg.VECTOR_COUNT} how many search to return
    
    # stuff document : It takes a list of documents, inserts them all into a prompt and passes that prompt to an LLM. 
    # https://python.langchain.com/docs/modules/chains/document/stuff
    
    qa_chain = RetrievalQA.from_chain_type(llm=llm,
                                       chain_type='stuff',
                                       retriever=vectordb.as_retriever(search_kwargs={'k': cfg.VECTOR_COUNT}),
                                       return_source_documents=cfg.RETURN_SOURCE_DOCUMENTS,
                                       chain_type_kwargs={'prompt': qa_prompt}
                                       )
    return qa_chain

def qa_bot(selected_model_name = "llama-2-7b-chat.ggmlv3.q8_0.bin"):
    # setup QA Bot
    
    embeddings = get_sentence_transformer()
    vectordb = FAISS.load_local(cfg.DB_FAISS_PATH, embeddings)
    
    llm = build_llm(selected_model_name)
    qa_prompt = set_custom_prompt()
    
    qa_bot = build_retrieval_qa(llm, qa_prompt, vectordb)

    return qa_bot

# def final_response(query, selected_model_name = "llama-2-7b-chat.ggmlv3.q8_0.bin"):
#     qa_result = qa_bot(selected_model_name)
#     response = qa_result({'query' : query})
#     return response
# ->