from pydantic import BaseModel


class Config(BaseModel):
    api_url: str = "http://127.0.0.1:10086/"
    plugin_enabled: bool = True
