import logging
import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from slack_bolt import BoltRequest
import openai
import pinecone
from sentence_transformers import SentenceTransformer
import re
import numpy as np

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Get environment variables from .env file
load_dotenv()
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment="us-west4-gcp")
pinecone_index = pinecone.Index("pdf")

# Load the pre-trained model
model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')

def encode_query(text):
    # Generate the sentence embedding
    embedding = model.encode(text)

    # Concatenate two copies of the same embedding to achieve the desired dimension
    query_vector = np.concatenate([embedding, embedding])

    return query_vector

def query_chatgpt(query):
   # Encode text query to a vector
    query_vector = encode_query(query)

    # Convert ndarray to a Python list
    query_vector = query_vector.tolist()

    # Query Pinecone
    pinecone_response = pinecone_index.query(queries=[query_vector], top_k=8)

    # Extract results from the Pinecone response
    pinecone_results = list(pinecone_response.query_results.values())[0]

    if not pinecone_results:
        return "I couldn't find any results for your query."

    # Format Pinecone results into a human-readable list
    formatted_results = "\n".join([f"{i+1}. {result}" for i, result in enumerate(pinecone_results)])

    # Ask GPT to provide a natural language response based on the Pinecone results
    gpt_query = f"Provide a natural language response based on these search results:\n\n{formatted_results}"
    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.6,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": gpt_query}
        ]
    )

    # Extract the assistant's reply from the response
    assistant_reply = gpt_response.choices[0].message['content']
    return assistant_reply

@app.event("app_mention")
def handle_search(body, say):
    app.logger.info("Inside handle_search")
    text = body['event'].get('text')
    query = re.sub(r'<@U[A-Z0-9]+>', '', text).strip()

    if not query:
        app.logger.info("No query provided")
        say('Please provide a search query.')
    else:
        app.logger.info(f"Query found: {query}")
        results = query_chatgpt(query)

        if results is None:
            response_text = f"No results found for '{query}'."
            app.logger.info(f"No results found for '{query}'.")
        else:
            response_text = f"{results}\n"
            app.logger.info(f"Found {len(results)} results")
        say(response_text)

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN, logger=app.logger)
    handler.start()