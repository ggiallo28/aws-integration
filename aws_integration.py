from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field, model_validator
from typing import Optional
import boto3

AWS_ACCES_KEY_LEN = 20
AWS_SECRET_ACCES_KEY_LEN = 40


class AWSClientSettings(BaseModel):
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    region_name: str = Field(default="us-east-1")
    credentials_profile_name: str = Field(default="")
    endpoint_url: str = Field(default="")

    @model_validator(mode="after")
    def validate(cls, v):
        session = boto3.Session()
        available_regions = session.get_available_regions("ec2")
        if v.region_name not in available_regions:
            raise ValueError(f"{v.region_name} is not a valid AWS region")

        if not v.credentials_profile_name:
            if not v.aws_access_key_id or not v.aws_secret_access_key:
                raise ValueError(
                    "Either provide a credentials profile name or both aws_access_key_id and aws_secret_access_key"
                )
            elif not (
                len(v.aws_access_key_id) == AWS_ACCES_KEY_LEN
                and len(v.aws_secret_access_key) == AWS_SECRET_ACCES_KEY_LEN
            ):
                raise ValueError("The access key or secret access key is invalid!")
        return v

    class Config:
        extra = "forbid"
        anystr_strip_whitespace = True


@plugin
def settings_model():
    return AWSClientSettings
