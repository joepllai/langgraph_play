import os


class DatabaseConfig:
    """
    Class to hold PostgreSQL database configuration.
    Environment variables are used to set the configuration values.
    """

    PSQL_USER = os.getenv("PSQL_USER")
    PSQL_PASSWORD = os.getenv("PSQL_PASSWORD")
    PSQL_HOSTNAME = os.getenv("PSQL_HOSTNAME")
    PSQL_PORT = os.getenv("PSQL_PORT")
    PSQL_VECTOR_STORE_DB = os.getenv("PSQL_VECTOR_STORE_DB", "langchain")
