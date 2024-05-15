from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field, model_validator
from typing import Optional
import boto3

AWS_ACCES_KEY_LEN = 20
AWS_SECRET_ACCES_KEY_LEN = 40


class AWSClientSettings(BaseModel):
    aws_access_key_id: str = Field(default="", description="AWS access key ID for authentication.")
    aws_secret_access_key: str = Field(default="", description="AWS secret access key for authentication.")
    region_name: str = Field(default="us-east-1", description="Default AWS region for the client.")
    credentials_profile_name: str = Field(default="", description="Name of the AWS credentials profile to use.")
    endpoint_url: str = Field(default="", description="Custom endpoint URL, if using a non-standard AWS service endpoint.")
    iam_role_assigned: bool = Field(default=False, description="Indicates if the required IAM role is assigned.")

    @model_validator(mode="after")
    def validate(cls, v):
        session = boto3.Session()
        available_regions = session.get_available_regions("ec2")
        if v.region_name not in available_regions:
            raise ValueError(f"{v.region_name} is not a valid AWS region")
        
        if not v.iam_role_assigned:
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
