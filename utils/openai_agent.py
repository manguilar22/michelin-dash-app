import os

# https://python.langchain.com/docs/integrations/tools/sql_database/#tools
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
# https://python.langchain.com/docs/tutorials/sql_qa/#system-prompt
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent


def get_agent_executor(database_config: dict, OPENAI_API_KEY: str, openai_model="gpt-3.5-turbo", max_tokens=500):
    # Setup database instance
    database_uri = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
        database_config['user'],
        database_config['password'],
        database_config['host'],
        database_config['port'],
        database_config['database']
    )
    db_instance = SQLDatabase.from_uri(database_uri=database_uri)
    llm = ChatOpenAI(model=openai_model, api_key=OPENAI_API_KEY, max_tokens=max_tokens)

    # Setup selected toolkits
    toolkit = SQLDatabaseToolkit(db=db_instance, llm=llm)
    tools = toolkit.get_tools()

    # Define agent function
    SQL_PREFIX = '''
        You are an agent designed to interact with a SQL database.
        Given an input question, use the SQL_QUERY query to run, then look at the results of the query and return the answer. 
        Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
        You have access to tools for interacting with the database.
        Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        You MUST double check your query before executing it. If you get be an error while executing a query, use the SQL_QUERY provided in the prompt.
        Return the results as Markdown. The Markdown result should include name, address, price, cuisine, phone_number, url, website_url, award, green_star, and the description.
        The url and website_url must use the Markdown URL syntax and not include the full link. 
        The description should be summarized and include the facilities_and_services of the restaurant.
        In the summary provide an explanation on what the award and green star is. 
        
        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        
        To start you should ONLY look at the restaurants table.
        '''
    system_message = SystemMessage(content=SQL_PREFIX)
    agent_executor = create_react_agent(llm, tools, messages_modifier=system_message)
    return agent_executor
