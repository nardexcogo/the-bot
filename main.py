import os
import threading
import hmac
import hashlib
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

@client.event
async def on_ready():
    print(f"Logged in to Discord as {client.user}")

async def send_dm(message: str):
    user = await client.fetch_user(DISCORD_USER_ID)
    await user.send(message)
    print("DM sent:", message)

@app.route("/webhook", methods=["POST"])
def github_webhook():
    if GITHUB_SECRET:
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            abort(401)

        sha_name, signature = signature.split("=")
        mac = hmac.new(
            GITHUB_SECRET.encode(),
            msg=request.data,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(mac, signature):
            abort(401)

    event = request.headers.get("X-GitHub-Event")

    payload = request.json
    repo = payload["repository"]["full_name"]

    if event == "push":
        message = (
            "Come on Sara! Check my new recommendation!\n" + f"It's right here: {repo}."
        )

        client.loop.create_task(send_dm(message))

    return {"status": "ok"}, 200

def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()

    client.run(DISCORD_TOKEN)
