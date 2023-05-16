# SlackGPT

## About
- Sets up a Slack chatbot that will take all @mentions of its username and query gpt-3.5-turbo with the text in the mention. It will then respond in the channel it was asked with the chatgpt response.

## Installation
- [TODO] explain setting up a slack bot in the slack api
- Place the following in the .env file: SLACK_APP_TOKEN, SLACK_BOT_TOKEN, OPEN_API_KEY
- [TODO] talk about creating a new python environment here
- Install the following with pip: openai, python-dotenv, slack-bolt
- python slacknerd.py
