import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str = "8862607230:AAGIJxaBzKmSefeU7u4pldyvGnFGmHM2YMo"
    ADMIN_IDS: List[int] = [233915651]
    
    # Database
    DATABASE_URL: str = "sqlite:///./echo_vpn.db"  # برای توسعه
    
    # Payment
    CARD_NUMBER: str = "6037-9912-3456-7890"
    CARD_OWNER: str = "ECHO VPN"
    
    # Support
    SUPPORT_USERNAME: str = "EchoVpnShopBot"
    SUPPORT_LINK: str = "https://t.me/EchoVpnShopBot"
    
    # Timezone
    TIMEZONE: str = "Asia/Tehran"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"
    
    # Rate Limits
    BROADCAST_RATE_LIMIT: int = 30
    MAX_RETRY_ATTEMPTS: int = 3
    
    # Development
    DEBUG: bool = False
    
    @validator('ADMIN_IDS', pre=True)
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
