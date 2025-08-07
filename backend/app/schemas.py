from pydantic import BaseModel

# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str
