from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from app.config.agent import AzureFoundryConfig
from openai import AzureOpenAI

gemini_2_5 = init_chat_model(
    model="gemini-2.5-flash-preview-05-20",
    model_provider="google_genai",
    temperature=0,
)

azure_foundry_gpt_4o = ChatOpenAI(
    model=AzureFoundryConfig.MODEL,
    api_key=AzureFoundryConfig.API_KEY,
    base_url=AzureFoundryConfig.BASE_URL,
    temperature=AzureFoundryConfig.TEMPERATURE,
    
)
# mle_model_qwen = ChatOpenAI(
#     model_name="/mnt/shared/copilot/chat/Qwen3-8B-16k-aics-chat",
#     api_key="example",
#     top_p=0.7,
#     temperature=0.8,
#     base_url="https://swift-tender-jawfish.ngrok-free.app/qwen3",
# )

# asus_aoc_gpt = AsusAOCGPT(
#     api_key=AOCConfig.API_KEY,
#     assistant_id=AOCConfig.ASSISTANT_ID,
#     service=AOCConfig.SERVICE,
#     version=AOCConfig.VERSION,
#     timeout=AOCConfig.TIMEOUT,
# )

import os
from openai import AzureOpenAI

endpoint = "https://cdp-ai-foundry.cognitiveservices.azure.com/"
model_name = "gpt-4o"
deployment = "gpt-4o"

subscription_key = "my key"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "I am going to Paris, what should I see?",
        }
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model=deployment
)

print(response.choices[0].message.content)