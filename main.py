import os
import threading
import hmac
import hashlib
import queue

from flask import Flask, request, abort
import discord
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_USER_ID = int(os.getenv("DISCORD_USER_ID"))
GITHUB_SECRET = os.getenv("GITHUB_SECRET")

app = Flask(__name__)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

dm_queue = queue.Queue()

@client.event
async def on_ready():
    print(f"Logged in to Discord as {client.user}")
    client.loop.create_task(dm_worker())

async def send_dm(message: str):
    try:
        print("Fetching user...")
        user = await client.fetch_user(DISCORD_USER_ID)

        print(f"Attempting to DM: {user}")

        await user.send(message)

        print("DM sent successfully")

    except Exception as e:
        print("Error sending DM:", type(e), e)

async def dm_worker():
    await client.wait_until_ready()

    print("DM worker started.")

    while True:
        message = dm_queue.get()

        print("Got message from queue:", message)

        try:
            await send_dm(message)
        except Exception as e:
            print("Worker failed to send DM:", e)

@app.route("/webhook", methods=["POST"])
def github_webhook():

    print("Webhook received")

    if GITHUB_SECRET:
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            print("Missing signature")
            abort(401)

        sha_name, signature = signature.split("=")
        mac = hmac.new(
            GITHUB_SECRET.encode(),
            msg=request.data,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(mac, signature):
            print("Bad signature")
            abort(401)

    event = request.headers.get("X-GitHub-Event")
    payload = request.json
    repo = payload["repository"]["full_name"]

    print("GitHub Event:", event)
    print("Repo:", repo)

    if event == "push":
        message = (
            "Come on Sara! Check my new recommendation!\n"
            f"It's right here: {repo}."
        )

        print("Queuing DM:", message)
        dm_queue.put(message)

    return {"status": "ok"}, 200

@app.route("/test_dm")
def test_dm():
    msg = "This is a test DM from Flask."
    print("Queuing test DM")
    dm_queue.put(msg)
    return "Test DM queued"

def run_flask():
    port = int(os.getenv("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    client.run(DISCORD_TOKEN)
