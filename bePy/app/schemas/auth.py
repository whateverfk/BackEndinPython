from pydantic import BaseModel, Field

class RegisterDto(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)

class LoginDto(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str

class ChangePasswordDto(BaseModel):
    old_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)