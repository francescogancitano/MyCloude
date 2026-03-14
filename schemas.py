from pydantic import BaseModel, Field
from typing import Optional

# base user schema
class UserBase(BaseModel):
    username: str

# schema for user creation (input)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# public schema for api output
class User(UserBase):
    id: int

    class Config:
        from_attributes = True

# full schema for database model (includes hash)
class UserInDB(User):
    password_hash: str

# schema for token data
class TokenData(BaseModel):
    username: Optional[str] = None

# schema for the access token response
class Token(BaseModel):
    access_token: str
    token_type: str

# schema for device metrics
class Device(BaseModel):
    cpuUsedPct     : Optional[float] = None
    cpuTemperature : Optional[float] = None
    ramUsedInMb  : Optional[float] = None
    ramTotalInMb : Optional[float] = None
    ramUsedInPct : Optional[float] = None
    diskUsedInMb  : Optional[float] = None
    diskTotalInMb : Optional[float] = None
    diskUsedInPct : Optional[float] = None
    networkTrafficIn  : Optional[float] = None
    networkTrafficOut : Optional[float] = None
    status : Optional[str] = None
