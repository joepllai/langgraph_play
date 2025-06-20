from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from app.agent.models.aooc import AsusAOCGPT
from app.config.agent import AOCConfig

gemini_2_5 = init_chat_model(
    model="gemini-2.5-flash-preview-05-20",
    model_provider="google_genai",
    temperature=0,
)

mle_model_qwen = ChatOpenAI(
    model_name="/mnt/shared/copilot/chat/Qwen3-8B-16k-aics-chat",
    api_key="example",
    top_p=0.7,
    temperature=0.8,
    base_url="https://swift-tender-jawfish.ngrok-free.app/qwen3",
)

asus_aoc_gpt = AsusAOCGPT(
    api_key=AOCConfig.API_KEY,
    assistant_id=AOCConfig.ASSISTANT_ID,
    service=AOCConfig.SERVICE,
    version=AOCConfig.VERSION,
    timeout=AOCConfig.TIMEOUT,
)