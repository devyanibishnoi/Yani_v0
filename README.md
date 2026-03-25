# Yani

**Yani** is a reflective AI system designed to help users understand themselves more clearly over time.

Rather than acting as a traditional chatbot or journaling tool, Yani functions as a **thinking partner** — noticing what matters, surfacing meaningful patterns, and gently guiding deeper reflection through conversation.

---

## Overview

Most tools for self-reflection either:

* reduce experiences to labels (mood trackers), or
* over-analyse without feeling natural

Yani is built to sit in between.

It focuses on:

* **selective insight over full analysis**
* **depth over volume**
* **reflection over advice**

The goal is not to explain the user —
but to help them **see something they hadn’t fully noticed before**.

---

## Current Version (v0)

This repository contains the first working version of Yani.

### Core capabilities

* Responds with **one focused observation**
* Asks **one meaningful question**
* Adapts to user tone and energy
* Maintains short-term conversational context
* Uses light memory from recent entries

---

## Tech Stack

* Flask (Python)
* Groq API
* SQLite
* HTML (Jinja templates)

---

## Running Locally

```bash
git clone https://github.com/devyanibishnoi/Yani_v0.git
cd Yani_v0
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

Run:

```bash
python app.py
```

---

## Philosophy

Yani is intentionally:

* non-prescriptive
* non-diagnostic
* user-led

It helps you **notice**, not tells you what to do.

---

## Status

This is v0 — focused on core interaction quality.

---

## Author

Built by Devyani Bishnoi
