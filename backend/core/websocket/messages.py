"""
ⒸAngelaMos | 2026
messages.py
"""

from datetime import datetime
from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

from models.Upload import ProcessingStatus


class ProcessingStage(str, Enum):
    """
    Granular processing stages within each status
    """
    QUEUED = "queued"
    EXTRACTING_FRAMES = "extracting_frames"
    VISION_ANALYSIS = "vision_analysis"
    DESCRIPTION_AUDIT = "description_audit"
    EMBEDDING_GENERATION = "embedding_generation"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


# Server
class UploadProgressPayload(BaseModel):
    """
    Detailed progress information for an upload
    """
    upload_id: str = Field(description="Upload UUID")
    status: ProcessingStatus = Field(description="Current processing status")
    stage: ProcessingStage = Field(description="Current processing stage")
    progress_percent: int = Field(
        ge=0,
        le=100,
        description="Progress percentage"
    )
    message: str = Field(description="Human-readable progress message")
    error_message: str | None = Field(
        default=None,
        description="Error details if failed"
    )
    description_audit_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Description quality score"
    )


class UploadProgressUpdate(BaseModel):
    """
    Real-time progress update message
    """
    action: Literal["upload_progress"] = "upload_progress"
    payload: UploadProgressPayload
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UploadCompleted(BaseModel):
    """
    Upload processing completed successfully
    """
    action: Literal["upload_completed"] = "upload_completed"
    upload_id: str
    description: str
    audit_score: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UploadFailed(BaseModel):
    """
    Upload processing failed
    """
    action: Literal["upload_failed"] = "upload_failed"
    upload_id: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuthSuccess(BaseModel):
    """
    WebSocket authentication succeeded
    """
    action: Literal["auth_success"] = "auth_success"
    user_id: str


class AuthError(BaseModel):
    """
    WebSocket authentication failed
    """
    action: Literal["auth_error"] = "auth_error"
    message: str


class Heartbeat(BaseModel):
    """
    Keep alive ping message
    """
    action: Literal["ping"] = "ping"


ServerMessage = Union[
    UploadProgressUpdate,
    UploadCompleted,
    UploadFailed,
    AuthSuccess,
    AuthError,
    Heartbeat,
]


# Client
class AuthMessage(BaseModel):
    """
    Initial authentication message from client
    """
    type: Literal["auth"] = "auth"
    token: str


class SubscribeUpload(BaseModel):
    """
    Subscribe to upload progress updates
    """
    action: Literal["subscribe_upload"] = "subscribe_upload"
    upload_id: str


class UnsubscribeUpload(BaseModel):
    """
    Unsubscribe from upload progress updates
    """
    action: Literal["unsubscribe_upload"] = "unsubscribe_upload"
    upload_id: str


class Pong(BaseModel):
    """
    Response to ping heartbeat
    """
    action: Literal["pong"] = "pong"


ClientMessage = Union[
    AuthMessage,
    SubscribeUpload,
    UnsubscribeUpload,
    Pong,
]

