import os, re
from slack_bolt import App
from slack_sdk import WebClient

# Load from Render Environment Variables
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
client = WebClient(token=SLACK_BOT_TOKEN)

# Store quiz progress + scores
user_progress = {}
user_scores = {}

# Hogwarts quiz (5 questions)
quiz = [
    {"q": "What matters most to you?",
     "options": {"1": "gryffindor", "2": "slytherin", "3": "ravenclaw", "4": "hufflepuff"},
     "labels": {"1": "Bravery 🦁", "2": "Cunning 🐍", "3": "Knowledge 🦅", "4": "Loyalty 🦡"}},
    {"q": "Pick a magical creature:",
     "options": {"1": "gryffindor", "2": "slytherin", "3": "ravenclaw", "4": "hufflepuff"},
     "labels": {"1": "Phoenix 🔥", "2": "Basilisk 🐍", "3": "Eagle 🦅", "4": "Niffler 🦡"}},
    {"q": "Choose your favorite class:",
     "options": {"1": "ravenclaw", "2": "gryffindor", "3": "slytherin", "4": "hufflepuff"},
     "labels": {"1": "Charms ✨", "2": "Defense ⚔️", "3": "Potions 🧪", "4": "Herbology 🌱"}},
    {"q": "Which color do you prefer?",
     "options": {"1": "gryffindor", "2": "slytherin", "3": "ravenclaw", "4": "hufflepuff"},
     "labels": {"1": "Red ❤️", "2": "Green 💚", "3": "Blue 💙", "4": "Yellow 💛"}},
    {"q": "Your ideal weekend is spent…",
     "options": {"1": "gryffindor", "2": "slytherin", "3": "ravenclaw", "4": "hufflepuff"},
     "labels": {"1": "Adventuring 🗡️", "2": "Scheming 🐍", "3": "Reading 📚", "4": "Relaxing ☕"}}
]

# Replace with your actual channel IDs (from Slack)
house_channels = {
    "gryffindor": "CXXXXGRYFFINDOR",
    "slytherin": "CXXXXSLYTHERIN",
    "ravenclaw": "CXXXXRAVENCLAW",
    "hufflepuff": "CXXXXHUFFLEPUFF"
}

# Command to start quiz
@app.message("sort me")
def start_quiz(message, say):
    user = message['user']
    user_progress[user] = 0
    user_scores[user] = {"gryffindor":0,"slytherin":0,"ravenclaw":0,"hufflepuff":0}
    say(f"🎩 Welcome <@{user}>! The Sorting Hat quiz begins...")
    ask_question(user, say)

# Ask a question
def ask_question(user, say):
    idx = user_progress[user]
    q = quiz[idx]
    options = "\n".join([f"{k}. {v}" for k,v in q["labels"].items()])
    say(f"*Q{idx+1}:* {q['q']}\n{options}\n👉 Reply with 1, 2, 3, or 4")

# Record answers
@app.message(re.compile("^[1-4]$"))
def record_answer(message, say, context):
    user = message['user']
    if user not in user_progress: return
    idx = user_progress[user]
    choice = context['matches'][0]

    q = quiz[idx]
    house = q["options"][choice]
    user_scores[user][house] += 1

    # Next or finish
    if idx + 1 < len(quiz):
        user_progress[user] += 1
        ask_question(user, say)
    else:
        finish_quiz(user, say)

# Finish scoring
def finish_quiz(user, say):
    scores = user_scores[user]
    top = max(scores.values())
    top_houses = [h for h,v in scores.items() if v == top]

    if len(top_houses) == 1:
        assign_house(user, top_houses[0], say)
    else:
        choices = " or ".join([h.title() for h in top_houses])
        say(f"🎩 Hmm… tough choice! You fit both *{choices}*.\n👉 Type the house name you choose.")
        user_progress[user] = "tie:" + ",".join(top_houses)

# Tie-break handling
@app.message(re.compile("gryffindor|slytherin|ravenclaw|hufflepuff", re.I))
def tie_break(message, say, context):
    user = message['user']
    if isinstance(user_progress.get(user), str) and user_progress[user].startswith("tie:"):
        choice = context['matches'][0].lower()
        if choice in user_progress[user]:
            assign_house(user, choice, say)

# Assign final house
def assign_house(user, house, say):
    say(f"🎩 The Sorting Hat has spoken: <@{user}> is in *{house.title()}*! 🦁🐍🦅🦡")
    try:
        client.conversations_invite(channel=house_channels[house], users=user)
    except Exception as e:
        say(f"(Could not auto-invite. Please join {house.title()} manually.)")
    user_progress.pop(user, None)
    user_scores.pop(user, None)

# Render entry point
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
