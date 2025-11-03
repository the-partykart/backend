from pydantic_settings import BaseSettings ,SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from environment variables.
    """

    log_mode : str
    graylog_host : str
    graylog_port : int

    secret_key : str
    algorithm : str 
    access_token_expire_minutes : int

    db_name : str
    db_drivername : str  
    db_username : str
    db_password : str
    db_port : int
    db_database_name : str
    db_server : str 

    global_prefix: str

    cloud_name : str
    api_key : str
    api_secret :str 
    secure : str

    AZURE_STORAGE_CONNECTION_STRING : str

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = 'allow'

settings = Settings()