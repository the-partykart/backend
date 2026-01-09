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

    GMAIL_USER : str
    GMAIL_APP_PASSWORD : str

    BIGSHIP_BASE_URL : str
    BIGSHIP_USERNAME : str
    BIGSHIP_PASSWORD : str
    BIGSHIP_ACCESS_KEY : str
 
    BIGSHIP_WAREHOUSE_ID : int

    BIGSHIP_PICKUP_LOCATION_ID : int
    BIGSHIP_RETURN_LOCATION_ID : int

    RATE_LIMIT_SLEEP : float

    BASE_URL :str
    USERNAME : str
    PASSWORD : str
    ACCESS_KEY : str


    PAYTM_ENV : str
    PAYTM_MID : str
    PAYTM_MERCHANT_KEY : str
    PAYTM_WEBSITE : str
    PAYTM_CALLBACK_URL : str

    PAYTM_FORCE_SUCCESS : str


    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = 'allow'

settings = Settings()