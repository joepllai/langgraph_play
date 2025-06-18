from langfuse import Langfuse
from app.config.langfuse import LangfuseConfig

langfuse = Langfuse(
  secret_key=LangfuseConfig.LANGFUSE_SECRET_KEY,
  public_key=LangfuseConfig.LANGFUSE_PUBLIC_KEY,
  host=LangfuseConfig.LANGFUSE_HOST,
)
