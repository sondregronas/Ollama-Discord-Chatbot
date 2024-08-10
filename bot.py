import ollama
import os
import discord
import re
from dotenv import load_dotenv


load_dotenv()

MODEL_NAME = os.getenv('MODEL_NAME')
AI_NAME = os.getenv('AI_NAME')
MAX_CONTENT_LEN = 250


def generate_response(text: str, context_messages: list) -> str | None:
    """Generate a response from the AI model based on the input text and context messages."""
    instructions = f"""
Your name is {AI_NAME}.

Only respond in short form (one sentence or so) as you are chatting in a chatroom, you don't need to repeat the name of the person you are responding to or worry about punctuation, capitalization or proper grammar. Write like you are a human chatting in a chatroom and not a bot.

Respond to the following message, the name of the person who sent it is in front of the colon. Do not include MESSAGE_START or MESSAGE_END in your response:

MESSAGE_START

{text}

MESSAGE_END

Here is some context you can base your response on, but it might not be relevant. You should only take the first couple of lines into account, but you can use more if you want to. The most recent messages are at the bottom:

{"\n".join(context_messages[-5:])}

"""

    try:
        return ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': instructions}])['message']['content']
    except Exception:
        return 'Failed to generate a response :('


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
context = list()


def add_to_context(sender, message):
    global context
    if len(context) > MAX_CONTENT_LEN:
        context.pop(0)
    context.append(f'{sender}: {message}')


@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    """If the bot was @mentioned, respond to the message."""
    add_to_context(message.author.global_name, message.content)

    if message.author == client.user:
        return

    mentioned = client.user.mentioned_in(message)

    if not mentioned:
        mentioned = bool(re.search(rf'\b{AI_NAME.lower()}\b', message.content.lower(), flags=re.MULTILINE))

    if mentioned:
        response = generate_response(f'{message.author.global_name}: {message.content}', context)
        await message.channel.send(response)


@tree.command(name='reset', description='Reset the context cache.')
async def _reset(ctx):
    global context
    context = list()
    await ctx.response.send_message('Context cache reset. I will now forget all previous messages.')

client.run(os.getenv('DISCORD_TOKEN'))
