import logging
import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from slack_bolt import BoltRequest
import openai
import re


# Initialize logging
logging.basicConfig(level=logging.INFO)

# Get environment variables from .env file
load_dotenv()
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

def query_chatgpt(query):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.6,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{query}"}
        ]
    )
    # Extract the assistant's reply from the response
    assistant_reply = response.choices[0].message['content']
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