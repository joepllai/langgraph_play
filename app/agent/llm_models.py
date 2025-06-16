from langchain.chat_models import init_chat_model

gemini_2_5 = init_chat_model(
    model="gemini-2.5-flash-preview-05-20",
    model_provider="google_genai",
    temperature=0,
)
