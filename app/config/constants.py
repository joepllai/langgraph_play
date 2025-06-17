from enum import Enum

API_PREFIX = "/api"


class Route:
    V1 = f"{API_PREFIX}/v1"


class TextSplitterType(str, Enum):
    RecursiveCharacterTextSplitter = "RecursiveCharacterTextSplitter"
    TextSplitter = "TextSplitter"
    Tokenizer = "Tokenizer"
    Language = "Language"
    RecursiveJsonSplitter = "RecursiveJsonSplitter"
    LatexTextSplitter = "LatexTextSplitter"
    PythonCodeTextSplitter = "PythonCodeTextSplitter"
    KonlpyTextSplitter = "KonlpyTextSplitter"
    SpacyTextSplitter = "SpacyTextSplitter"
    NLTKTextSplitter = "NLTKTextSplitter"
    SentenceTransformersTokenTextSplitter = "SentenceTransformersTokenTextSplitter"
    ElementType = "ElementType"
    HeaderType = "HeaderType"
    LineType = "LineType"
    HTMLHeaderTextSplitter = "HTMLHeaderTextSplitter"
    MarkdownHeaderTextSplitter = "MarkdownHeaderTextSplitter"
    MarkdownTextSplitter = "MarkdownTextSplitter"
    CharacterTextSplitter = "CharacterTextSplitter"


class EmbeddingType(str, Enum):
    AzureOpenAIEmbeddings = "AzureOpenAIEmbeddings"
    GoogleGenerativeAIEmbeddings = "GoogleGenerativeAIEmbeddings"


class DefaultEmbeddingOptions:
    docs = []
    splitter = TextSplitterType.CharacterTextSplitter
    splitter_options = {}
    embedding_model = EmbeddingType.GoogleGenerativeAIEmbeddings
    embedding_model_options = {}
    output_dims = 1536


class RAGOptions:
    QUERY_NEAREST_EMBEDDING_LIMIT = 3
    HISTORY_NEAREST_EMBEDDING_LIMIT = 1
    DOCUMENT_LENGTH_LIMIT = 5000


class ChatRole:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContextVarKeys:
    USER = "user"
    OPID = "operation_id"
    USERNAME = "username"
