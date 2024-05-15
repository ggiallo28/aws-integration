from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field, model_validator
from typing import Optional
import boto3


class AWSClientSettings(BaseModel):
    aws_access_key_id: str = Field(default="", min_length=20, max_length=20)
    aws_secret_access_key: str = Field(default="", min_length=40, max_length=40)
    region_name: str = Field(default="us-east-1")
    credentials_profile_name: str = Field(default="")
    endpoint_url: str = Field(default="")

    @model_validator(mode="before")
    def validate_region(cls, v):
        session = boto3.Session()
        available_regions = session.get_available_regions("ec2")
        if v["region_name"] not in available_regions:
            raise ValueError(f"{v} is not a valid AWS region")
        return v

    class Config:
        extra = "forbid"
        anystr_strip_whitespace = True


@plugin
def settings_model():
    return AWSClientSettings
