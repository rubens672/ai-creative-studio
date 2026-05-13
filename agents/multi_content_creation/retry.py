"""Gemini retry config for handling 429 rate limits and transient errors.

Il modello pay-as-you-go utilizza la quota condivisa dinamica, quindi gli errori 429 possono verificarsi quando il pool condiviso è occupato. 
Sono necessari tentativi a livello di applicazione (l'SDK non li abilita per impostazione predefinita). 
Passa `generate_content_config=GENERATE_CONTENT_CONFIG` a ogni agente in modo che ogni chiamata al modello tenti con un backoff esponenziale prima di rinunciare.
"""

from google.genai import types

RETRY_CONFIG = types.HttpRetryOptions(
    attempts=3,
    exp_base=2,
    initial_delay=5,
    http_status_codes=[429, 500, 503, 504],
)

GENERATE_CONTENT_CONFIG = types.GenerateContentConfig(
    http_options=types.HttpOptions(
        retry_options=RETRY_CONFIG,
        timeout=120_000,  # 120 second timeout for model calls
    ),
)