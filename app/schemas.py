from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TeamMemberBase(BaseModel):
    user_id: str
    username: str
    is_active: bool


class TeamCreate(BaseModel):
    team_name: str
    members: List[TeamMemberBase]


class TeamResponse(BaseModel):
    team_name: str
    members: List[TeamMemberBase]
    
    class Config:
        from_attributes = True


class UserUpdateActive(BaseModel):
    user_id: str
    is_active: bool


class UserResponse(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool
    
    class Config:
        from_attributes = True


class PullRequestCreate(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class PullRequestMerge(BaseModel):
    pull_request_id: str


class PullRequestReassign(BaseModel):
    pull_request_id: str
    old_user_id: str


class PullRequestResponse(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str
    assigned_reviewers: List[str]
    created_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str
    
    class Config:
        from_attributes = True


class UserPRsResponse(BaseModel):
    user_id: str
    pull_requests: List[PullRequestShort]


class ErrorResponse(BaseModel):
    error: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "resource not found"
                }
            }
        }