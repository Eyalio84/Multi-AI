"""Structured backend specification for Claude Code consumption."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class DatabaseColumn(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    unique: bool = False
    nullable: bool = True
    default: Optional[str] = None


class DatabaseTable(BaseModel):
    name: str
    columns: List[DatabaseColumn]
    indexes: List[str] = []


class DatabaseSchema(BaseModel):
    type: str  # "sqlite", "postgresql", "mysql"
    tables: List[DatabaseTable]


class ApiEndpoint(BaseModel):
    method: str
    path: str
    summary: Optional[str] = None
    request_body: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    auth_required: bool = False


class DataModel(BaseModel):
    name: str
    fields: Dict[str, str]


class BackendSpec(BaseModel):
    version: str = "1.0"
    framework: str = "fastapi"
    language: str = "python"
    database: Optional[DatabaseSchema] = None
    endpoints: List[ApiEndpoint] = []
    models: Dict[str, DataModel] = {}
    dependencies: List[str] = []
    environment_variables: List[str] = []
