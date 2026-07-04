**`base.py`**

**`__init__(self, model: str)`**
- Abstract method
- Forces every connector that inherits from `AgentConnector` to accept a `model` parameter
- Does nothing itself — just enforces the rule
- Example: `NvidiaConnector(model="meta/llama-3.1-8b-instruct")`

**`send(self, prompt: str) -> str`**
- Abstract method
- Forces every connector to implement a `send` function
- Must accept a string prompt and return a string response
- Does nothing itself — just enforces the rule
- Body is just `pass`

---

**`nvidia_connector.py`**

**`__init__(self, model: str = "meta/llama-3.1-8b-instruct")`**
- Inherits from `AgentConnector` so satisfies base rule
- Sets `self.model` — which model to use on NVIDIA NIM
- Calls `load_dotenv()` — reads `.env` file
- Sets `self.api_key` — fetches `NVIDIA_API_KEY` from `.env`
- Sets `self.base_url` — NVIDIA NIM endpoint URL
- Has a default model so you can call `NvidiaConnector()` without arguments

**`send(self, prompt: str) -> str`**
- Inherits from `AgentConnector` so satisfies base rule
- Makes a `POST` request to NVIDIA NIM using `httpx`
- Sends the prompt inside `messages` array as role `user`
- Sets `max_tokens=1024` — limits response length
- Sets `timeout=30.0` — won't hang forever
- Calls `raise_for_status()` — catches bad HTTP responses
- Parses response and returns `choices[0].message.content` — the actual text
- Handles 4 errors:
    - `TimeoutException` — API too slow
    - `HTTPStatusError 401` — wrong API key
    - `HTTPStatusError 429` — too many requests
    - `NetworkError` — no internet