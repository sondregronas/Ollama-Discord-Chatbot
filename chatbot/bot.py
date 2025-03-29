import ollama
import os
import discord
import re
from dotenv import load_dotenv

from prompts import SHOULD_RESPOND_PROMPT, MESSAGE_PROMPT
from logger import logger

load_dotenv()

MAX_CONTENT_LEN = 30  # How many messages to keep in context
CONTEXT_SIZE = int(os.getenv("CONTEXT_SIZE", 4)) * 1024  # num_ctx size for the model

MODEL = os.getenv("MODEL", "gemma3:12b")  # The model to use for generating responses
OLLAMA_SERVER = os.getenv("OLLAMA_SERVER", "127.0.0.1")
AI_NAMES = os.getenv("AI_NAMES").split(
    ","
)  # Used to identify when the bot is mentioned
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
OLLAMA_OPTIONS = {
    "num_ctx": CONTEXT_SIZE,
    "temperature": 0.9,
    "top_k": 50,
    "top_p": 0.9,
    "repeat_last_n": -1,
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
context = list()


ollama_client = ollama.Client(OLLAMA_SERVER)
try:
    ollama_client.show(MODEL)
except ollama._types.ResponseError:
    ollama_client.pull(MODEL)
except Exception as e:
    logger.error(f"Failed to connect to Ollama: {e}")


def _generate(prompt: str) -> str:
    try:
        r = ollama_client.generate(
            model=MODEL,
            prompt=prompt,
            system=SYSTEM_PROMPT,
            options=OLLAMA_OPTIONS,
        ).response
        logger.debug(f"Prompt: {prompt}\nResponse: {r}")
        return r
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        return "Failed to generate a response :("


def _should_respond_prompt(text: str) -> bool:
    """Check if the bot should respond to the message."""
    bot_messages = ""
    for msg in context:
        if msg.startswith(client.user.name + ": "):
            bot_messages += msg + "\n"

    prompt = SHOULD_RESPOND_PROMPT.format(
        **{
            "ai_name": AI_NAMES[0],
            "text": text,
            "system_prompt": SYSTEM_PROMPT,
            "bot_messages": bot_messages,
        }
    )
    p = _generate(prompt)
    p = "".join([ch for ch in p if ch.isalpha()])
    logger.info(f"Bot thought about responding: {p}")
    return p.lower().strip() == "yes"


def generate_response(text: str) -> str:
    """Generate a response from the AI model based on the input text and context messages."""
    prompt = MESSAGE_PROMPT.format(
        **{
            "ai_name": AI_NAMES[0],
            "earlier_messages": "\n".join(context),
            "text": text,
        }
    )
    return _generate(prompt)


def add_to_context(sender, message):
    global context
    if len(context) > MAX_CONTENT_LEN:
        context.pop(0)
    context.append(f"{sender}: {message}")


def should_respond(message) -> bool:
    """Check if the bot should respond to the message."""
    discord_mentioned = client.user.mentioned_in(message)

    name_mentioned = bool(
        re.search(
            rf"\b({'|'.join(AI_NAMES)})\b",
            message.content.lower(),
            flags=re.MULTILINE | re.IGNORECASE,
        )
    )

    message_directed_at_bot = _should_respond_prompt(message.content)

    logger.debug(
        f"Discord mentioned: {discord_mentioned}, "
        f"Name mentioned: {name_mentioned}, "
        f"Message directed at bot: {message_directed_at_bot}"
    )

    return any(
        [
            discord_mentioned,
            name_mentioned,
            message_directed_at_bot,
        ]
    )


@client.event
async def on_ready():
    await tree.sync()
    logger.info(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    """If the bot was @mentioned, respond to the message."""
    add_to_context(message.author.global_name, message.content)

    if message.author == client.user:
        return

    if should_respond(message):
        response = generate_response(f"{message.author.global_name}: {message.content}")
        await message.channel.send(response)


@tree.command(name="reset", description="Reset the context cache.")
async def _reset(ctx):
    global context
    context = list()
    await ctx.response.send_message(
        "Context cache reset. I will now forget all previous messages."
    )


client.run(os.getenv("DISCORD_TOKEN"))
