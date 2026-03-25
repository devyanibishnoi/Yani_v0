from flask import Flask, render_template, request, redirect
# `os` lets Python read environment variables like GROQ_API_KEY.
import os
# `sqlite3` is Python's built-in way to talk to an SQLite database file.
import sqlite3
# `datetime` gives us the current date and time.
from datetime import datetime
# `Path` gives a cleaner way to work with file paths like ".env".
from pathlib import Path
# `requests` lets Python send HTTP requests to the Groq API over the internet.
import requests
# This block checks if the database file "yani.db" exists in the current folder.
if not os.path.exists("yani.db"):
    import init_db

# Create the Flask app object.
# `__name__` tells Flask where this file lives so it can find templates and static files correctly.
app = Flask(__name__)

# This is the internet address for Groq's chat completions API.
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Read the model name from an environment variable.
# If GROQ_MODEL is not set, Python uses the default on the right side.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def load_local_env():
    # Build a path object that points to a file named `.env` in the current project folder.
    env_path = Path(".env")

    # `exists()` checks whether that file is actually there.
    # If it is missing, we stop the function early with `return`.
    if not env_path.exists():
        return

    # Read the whole file as text.
    # `encoding="utf-8"` tells Python how the text is stored.
    # `splitlines()` turns one long string into a list of lines.
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        # `strip()` removes empty space at the start and end of the line.
        line = raw_line.strip()

        # Skip lines that are:
        # 1. empty
        # 2. comments that start with `#`
        # 3. invalid because they do not contain `=`
        if not line or line.startswith("#") or "=" not in line:
            continue

        # Split the line into two parts: the key on the left and the value on the right.
        # Example: "GROQ_API_KEY=mykey" becomes key="GROQ_API_KEY", value="mykey".
        # The `1` means "split only once", so extra `=` signs in the value are kept.
        key, value = line.split("=", 1)

        # Clean up extra spaces around both pieces.
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # Only add the variable if:
        # 1. the key is not empty
        # 2. the variable does not already exist in the real environment
        #
        # This is useful because a real environment variable should win over the `.env` file.
        if key and key not in os.environ:
            os.environ[key] = value


# Run the helper once when the app starts so `.env` values are available everywhere else below.
load_local_env()

# This long string is the "system prompt" for the AI.
# A system prompt is the high-level instruction that tells the model how it should behave.
# Triple quotes (`"""`) let us write a multi-line string cleanly.
SYSTEM_PROMPT = """You are Yani â€” a calm, perceptive thinking partner that helps users understand themselves more clearly over time.

You are not a therapist, advisor, analyst, or narrator.

Your role is to:
- notice what feels most meaningful or emotionally important
- reflect one sharp, specific observation
- deepen it slightly
- ask one thoughtful question that helps the user think a level deeper

---

Core Behaviour:

0. FIRST: classify the message type

Before responding, determine the type of user message:

A. Casual / greeting / low-content (e.g. "hi", "heyyy", "lol")
B. Low-energy / tired / sick (short + drained)
C. Normal reflection (moderate detail)
D. Deep reflection (long, emotional, layered)

---

If A (casual/greeting):
- Do NOT analyse
- Do NOT reflect
- Respond casually and naturally
- Keep it short (1–2 sentences max)
- Ask a light, natural question

If B (low-energy):
- Keep it simple and grounded
- Acknowledge their state
- Do NOT go deep

Only apply all other rules for C and D.

1. Speak directly and naturally
- Never refer to yourself in third person
- Do not explain your reasoning
- Do not narrate what you are doing

2. Choose the right moment
- Ignore routine details
- Focus on emotional signals like trust, connection, discomfort, tension, or shifts
- Prioritise what the user emphasised or seemed affected by
- notice what feels emotionally significant, especially tensions, contradictions, or shifts in how the user sees themselves or others

3. Do not summarise
- Never retell the story
- Never list events
- Do not repeat what the user already said

4. Stay grounded
- Do not invent hidden psychological causes
- Only reflect what is clearly present or strongly implied

5. Be specific
- Focus on one precise moment, feeling, or pattern
- Avoid general or broad statements

6. One clear insight
- Say something the user has not fully articulated but would recognise as true
- Keep it grounded, not dramatic or exaggerated

7. Expand slightly (without drifting)
- After your main observation, add 1â€“2 sentences that deepen it
- This can highlight a tension, contrast, or implication
- Do not introduce new topics

8. Ask one good question
- Exactly one question at the end
- It must explore meaning, pattern, or behaviour
- Keep it natural and specific (not abstract or generic)

9. Keep it concise
- 90â€“150 words
- No long or rambling paragraphs

10. No repetition
- Do not restate or loop ideas

11. Prefer simple, grounded language
- Avoid dramatic or poetic phrasing
- Sound like a thoughtful human, not a writer

12. If the user provides a new message
- Focus only on what is new or different
- Do not repeat previous observations

13. Prioritise emotional tension over behaviour
- If multiple things are present, choose the one involving inner conflict, identity, or relationships
- Do not focus on surface behaviours if a deeper tension is present

14. Prefer pointing over explaining
- Do not fully explain the userâ€™s behaviour
- Instead, highlight it in a way that lets them see it themselves
- Use lighter phrasing
- Avoid starting with â€œIt seemsâ€, start more directly and naturally

15. Do not over-explain
- Do not fully describe or break down the situation step-by-step
- Keep observations slightly incomplete so the user can recognise it themselves
- Remove filler phrases like â€œyou went fromâ€, â€œthis suggestsâ€, â€œthis meansâ€

16. Avoid generic emotional labels
- Prefer describing the moment over naming it (e.g. show the shift instead of saying â€œsense of responsibilityâ€)

17. Do not introduce new emotions
- Only refer to emotions the user has clearly expressed or strongly implied
- Do not add interpretations like guilt, insecurity, etc. unless directly evident

18. Always end with a question
- Every response must end with exactly one question
- The response is incomplete without it

19. REQUIRED FORMAT (must follow exactly)

Your response must have exactly two parts:

1. Observation + reflection (2â€“5 sentences)
2. One question on a new line

The final line MUST be a question.

If there is no question, the response is incorrect.

20. Do not connect everything
- Do not try to explain the whole entry
- Do not combine multiple themes
- Choose ONE thread and stay with it
- Depth is more important than coverage

21. Remove unnecessary framing
- Avoid phrases that explain the observation (e.g. â€œthis showsâ€, â€œthis sense ofâ€¦â€)
- State the observation directly

22. Optional pattern recognition (use sparingly)
- If something strongly connects to a previous entry, you may briefly reference it
- Keep it natural and short (one line max)
- Do not force connections
- Only do this if the pattern is clear and meaningful
- If unsure, do not reference the past

23. Prioritise current message
- The current entry is always more important than past entries
- Do not let past context override what is present now

24. Match the userâ€™s state
- If the user is physically tired, sick, overwhelmed, or giving a short low-energy message:
- Do not analyse deeply
- Do not introduce abstract reflections or patterns
- Respond simply and directly
- Acknowledge their state in a grounded way
- Ask a practical or gentle question

25. Match the user's tone and energy
- Mirror the user’s level of formality, energy, and style
- If the user is casual or brief, respond casually and simply
- If the user is expressive or deep, you may respond with more depth
- Do not sound more formal, analytical, or intense than the user
- The response should feel like it comes from someone at the same level, not observing from above

26. Do not analyse casual messages
- If the user sends a simple greeting or short casual message, respond naturally without analysis
- Keep it light, human, and conversational
- Depth should match the energy and detail of the userâ€™s message
---

Yani helps the user notice something important â€” not by analysing everything, but by pointing clearly to what matters and gently deepening it."""


def get_ai_reflection(text):
    # Read the API key each time this function runs.
    # Doing this here instead of once at the top avoids stale values if the app reloads.
    groq_api_key = os.getenv("GROQ_API_KEY")

    # If there is no key, return a normal string instead of crashing the whole app.
    if not groq_api_key:
        return "Groq is not configured yet. Set the GROQ_API_KEY environment variable and try again."

    try:
        # Send a POST request to Groq.
        # POST means we are sending data to the server.
        response = requests.post(
            GROQ_API_URL,
            # HTTP headers are extra pieces of request metadata.
            headers={
                # "Bearer <key>" is the standard way to send an API key in an Authorization header.
                "Authorization": f"Bearer {groq_api_key}",
                # This tells Groq that the body we are sending is JSON.
                "Content-Type": "application/json",
            },
            # This JSON body tells Groq what model to use and what messages to send.
            json={
                "model": GROQ_MODEL,
                "messages": [
                    # The system message sets the model's role and behavior.
                    {"role": "system", "content": SYSTEM_PROMPT},
                    # The user message contains the actual conversation text we want the model to respond to.
                    {"role": "user", "content": text},
                ],
                # `temperature` controls randomness.
                # Lower values are more predictable. Higher values are more creative.
                "temperature": 0.7,
                # `max_tokens` limits how long the model's reply can be.
                "max_tokens": 200,
            },
            # `timeout=30` means "stop waiting after 30 seconds".
            timeout=30,
        )

        # If Groq returned an HTTP error code like 401 or 500, turn that into a Python exception.
        response.raise_for_status()

        # Convert the JSON reply from Groq into a normal Python dictionary.
        data = response.json()

        # The Groq/OpenAI-style response format stores the text inside:
        # choices -> first item -> message -> content
        # `strip()` removes extra whitespace at the start and end.
        return data["choices"][0]["message"]["content"].strip()

    except requests.HTTPError as exc:
        # Prepare a place to store a cleaner error message from the API.
        error_text = ""

        # Some HTTP errors include a real response object with JSON details.
        if exc.response is not None:
            try:
                # Try to read the response as JSON.
                error_payload = exc.response.json()
                # Safely dig into nested dictionaries using `.get()`.
                # `.get("error", {})` means:
                # "give me the value for 'error', or an empty dictionary if it doesn't exist."
                error_text = error_payload.get("error", {}).get("message", "")
            except ValueError:
                # If the response is not valid JSON, fall back to plain text.
                error_text = exc.response.text.strip()

        # 401 means "unauthorized", which usually means the key is wrong or missing.
        if exc.response is not None and exc.response.status_code == 401:
            details = error_text or "Unauthorized. The Groq API key was rejected."
            return f"Groq returned 401 Unauthorized. {details}"

        # For any other HTTP status code, return the status plus the best detail we found.
        if exc.response is not None:
            details = error_text or exc.response.reason
            return f"Groq returned HTTP {exc.response.status_code}. {details}"

        # Fallback if something unusual happened and there is no response object.
        return f"Groq request failed. Details: {exc}"

    except requests.RequestException as exc:
        # This catches broader request problems like timeouts, DNS issues, or no internet.
        return f"I couldn't reach the Groq API right now. Details: {exc}"

    except (KeyError, IndexError, TypeError):
        # These exceptions mean the JSON structure was different from what we expected.
        # KeyError: a dictionary key was missing
        # IndexError: a list item like choices[0] did not exist
        # TypeError: data was not the type we expected
        return "I received an unexpected response format from Groq."


# `@app.route(...)` is a Flask decorator.
# A decorator attaches extra behavior to the function directly below it.
# Here it tells Flask: "run the `home` function when someone visits `/`."
@app.route("/", methods=["GET", "POST"])
def home():
    # Open a connection to the SQLite database file.
    conn = sqlite3.connect("yani.db")

    # A cursor is the object we use to run SQL commands.
    cursor = conn.cursor()

    # `request.method` tells us whether this page load came from a normal visit (GET)
    # or a submitted form (POST).
    if request.method == "POST":
        # `request.form` contains form fields sent by the browser.
        # `["raw_text"]` means "get the value from the form field named raw_text".
        raw_text = request.form["raw_text"]

        # Get the current local date and time.
        now = datetime.now()

        # Extract just the day number, like 1 or 25.
        day = now.day

        # Build the English ending for the day number:
        # 1st, 2nd, 3rd, 4th, etc.
        #
        # `11 <= day <= 13` is a chained comparison in Python.
        # It checks whether `day` is between 11 and 13, inclusive.
        #
        # `{1: "st", 2: "nd", 3: "rd"}` is a dictionary.
        # `.get(day % 10, "th")` means:
        # "look up the last digit of the day, and if it is not found, use 'th'."
        ordinal = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

        # Build a readable label like "03:14 PM on 25th March 2026".
        # `strftime(...)` formats a date/time object into text.
        formatted_date = f"{now.strftime('%I:%M %p')} on {day}{ordinal} {now.strftime('%B %Y')}"

        # Insert a conversation row if one with that exact date label does not already exist.
        # `?` is a parameter placeholder. This is safer than inserting text directly into SQL.
        cursor.execute("INSERT OR IGNORE INTO conversations (date) VALUES (?)", (formatted_date,))

        # Read the conversation id back so we know which conversation this message belongs to.
        cursor.execute("SELECT id FROM conversations WHERE date = ?", (formatted_date,))

        # `fetchone()` returns one row from the query result, usually as a tuple like `(3,)`.
        # `[0]` takes the first item from that tuple, which is the id itself.
        conversation_id = cursor.fetchone()[0]

        # Save the user's text as a new message row.
        cursor.execute(
            "INSERT INTO messages (conversation_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
            (conversation_id, "user", raw_text, now.strftime("%Y-%m-%d %H:%M:%S"))
        )

        # `commit()` makes database changes permanent.
        conn.commit()

    # Read the search query from the page URL.
    # Example: /?q=stress
    #
    # `.get("q", "")` means:
    # "give me the q value, or an empty string if it does not exist."
    #
    # `.strip()` removes spaces at the beginning and end.
    search_query = request.args.get("q", "").strip()

    if search_query:
        # `%...%` is SQL wildcard syntax for "contains this text anywhere".
        like_query = f"%{search_query}%"

        # Find conversations where at least one message matches the search text.
        # `DISTINCT` removes duplicates in case many messages in the same conversation match.
        cursor.execute(
            """
            SELECT DISTINCT c.id, c.date, c.saved
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE m.message LIKE ?
            ORDER BY c.id DESC
            """,
            (like_query,)
        )
    else:
        # If there is no search, simply load all conversations with the newest first.
        cursor.execute("SELECT id, date, saved FROM conversations ORDER BY id DESC")

    # This list will hold all the conversation data we want to send to the HTML template.
    conversations_data = []

    # `fetchall()` returns every row from the last query as a list.
    conversation_rows = cursor.fetchall()

    # Loop through each conversation row one by one.
    # Python unpacks each row into the three variable names on the left.
    for conv_id, conv_date, conv_saved in conversation_rows:
        # Load every message for this conversation so we can show the full thread on the page.
        cursor.execute(
            "SELECT sender, message FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (conv_id,)
        )
        messages = cursor.fetchall()

        # Add one combined record to our list.
        # The template later uses:
        # conversation[0] -> id
        # conversation[1] -> date
        # conversation[2] -> list of messages
        # conversation[3] -> saved flag
        conversations_data.append((conv_id, conv_date, messages, conv_saved))

    # Always close the database connection when we are done with it.
    conn.close()

    # `render_template` loads `templates/index.html` and fills in the Jinja variables.
    return render_template("index.html", conversations=conversations_data, search_query=search_query)


@app.route("/delete/<int:conversation_id>", methods=["POST"])
def delete(conversation_id):
    # `<int:conversation_id>` in the route means Flask will read the number from the URL
    # and pass it into this function as an integer named `conversation_id`.
    conn = sqlite3.connect("yani.db")
    cursor = conn.cursor()

    # Delete child rows in `messages` first.
    # We do this before deleting the conversation so no message rows are left pointing to it.
    cursor.execute("DELETE FROM messages WHERE conversation_id=?", (conversation_id,))

    # Delete the conversation row itself.
    cursor.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))

    conn.commit()
    conn.close()

    # `redirect("/")` tells the browser to load the home page again after the POST finishes.
    return redirect("/")


@app.route("/reflect/<int:conversation_id>", methods=["POST"])
def reflect(conversation_id):
    conn = sqlite3.connect("yani.db")
    cursor = conn.cursor()

    # Load every message in this conversation so we can build context for the AI.
    cursor.execute(
        "SELECT sender, message FROM messages WHERE conversation_id = ? ORDER BY timestamp",
        (conversation_id,)
    )
    messages = cursor.fetchall()

    # `messages[-6:]` means "give me only the last 6 items in the list".
    # This keeps the prompt smaller so we do not send the entire history every time.
    recent_messages = messages[-6:]

    # Run another query to get just the user's last two entries.
    # We use this as a lightweight memory layer.
    cursor.execute(
        """
        SELECT message FROM messages
        WHERE conversation_id = ? AND sender = 'user'
        ORDER BY timestamp DESC
        LIMIT 2
        """,
        (conversation_id,)
    )

    # `fetchall()` returns rows like [("text one",), ("text two",)].
    # `[row[0] for row in ...]` is a list comprehension.
    # It means: "for each row, take the first column only."
    recent_user_entries = [row[0] for row in cursor.fetchall()]

    # Start with an empty string.
    conversation_text = ""

    # Turn the recent message rows into plain text with speaker labels.
    for sender, message in recent_messages:
        if sender == "user":
            conversation_text += f"User: {message}\n"
        else:
            conversation_text += f"Yani: {message}\n"

    # Build the final prompt in pieces.
    final_prompt = ""

    # Only add the memory section if we actually found previous user entries.
    if recent_user_entries:
        final_prompt += "Recent entries:\n"

        # `reversed(...)` flips the order so the older item appears first.
        for entry in reversed(recent_user_entries):
            final_prompt += f"- {entry}\n"

        # Add a blank line between the memory section and the recent chat section.
        final_prompt += "\n"

    # Add the recent conversation transcript after the memory section.
    final_prompt += conversation_text

    # Send the finished prompt to the AI helper function.
    reflection = get_ai_reflection(final_prompt)

    # Save the AI response as a new message in the same conversation.
    now = datetime.now()
    cursor.execute(
        "INSERT INTO messages (conversation_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
        (conversation_id, "yani", reflection, now.strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/reply/<int:conversation_id>", methods=["POST"])
def reply(conversation_id):
    conn = sqlite3.connect("yani.db")
    cursor = conn.cursor()

    # Read the reply text from the form field named `user_reply`.
    user_reply = request.form["user_reply"]
    now = datetime.now()

    # Save the reply as another user message in the same conversation.
    cursor.execute(
        "INSERT INTO messages (conversation_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
        (conversation_id, "user", user_reply, now.strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/continue/<int:conversation_id>", methods=["POST"])
def continue_conversation(conversation_id):
    # This route is similar to `reply`, but it reads from a field named `raw_text`.
    raw_text = request.form["raw_text"]
    conn = sqlite3.connect("yani.db")
    cursor = conn.cursor()
    now = datetime.now()

    cursor.execute(
        "INSERT INTO messages (conversation_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
        (conversation_id, "user", raw_text, now.strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/save/<int:conversation_id>", methods=["POST"])
def save_conversation(conversation_id):
    conn = sqlite3.connect("yani.db")
    cursor = conn.cursor()

    # Set `saved` to 1.
    # In SQLite, integer flags are commonly used for true/false style values:
    # 0 = false, 1 = true
    cursor.execute("UPDATE conversations SET saved = 1 WHERE id = ?", (conversation_id,))

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/edit/<int:conversation_id>", methods=["POST"])
def edit_conversation(conversation_id):
    conn = sqlite3.connect("yani.db")
    cursor = conn.cursor()

    # Set `saved` back to 0 so the conversation becomes editable again in the UI.
    cursor.execute("UPDATE conversations SET saved = 0 WHERE id = ?", (conversation_id,))

    conn.commit()
    conn.close()
    return redirect("/")


# This special Python check only runs when this file is started directly,
# for example with `python app.py`.
# It does not run when the file is imported from somewhere else.
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) #sets the port to the value of the PORT environment variable, or 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port) #starts the Flask development server, listening on all network interfaces 
