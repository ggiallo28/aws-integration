from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from cat.log import log
import boto3

AWS_ACCES_KEY_LEN = 20
AWS_SECRET_ACCES_KEY_LEN = 40
DEFAULT_REGION = "us-east-1"


class Boto3Builder:
    def __init__(
        self,
        region_name: str,
        service_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        iam_role_assigned: Optional[bool] = False,
    ):
        self.service_name = service_name
        self.profile_name = profile_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.endpoint_url = endpoint_url
        self.iam_role_assigned = iam_role_assigned
        self.region_name = region_name

    def set_profile_name(self, profile_name: str):
        self.profile_name = profile_name

    def set_credentials(self, aws_access_key_id: str, aws_secret_access_key: str):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def set_endpoint_url(self, endpoint_url: str):
        self.endpoint_url = endpoint_url

    def build_session(self):
        if self.iam_role_assigned:
            session = boto3.Session()
        elif self.profile_name:
            session = boto3.Session(profile_name=self.profile_name)
        else:
            session_kwargs = {}
            if self.aws_access_key_id and self.aws_secret_access_key:
                session_kwargs["aws_access_key_id"] = self.aws_access_key_id
                session_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
            session = boto3.Session(**session_kwargs)
        return session

    def _get_kwargs(self):
        kwargs = {
            "region_name": self.region_name,
        }
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        return kwargs

    def build_client(self, service_name):
        session = self.build_session()
        client_kwargs = self._get_kwargs()
        return session.client(self.service_name or service_name, **client_kwargs)

    def build_resource(self, service_name):
        session = self.build_session()
        resource_kwargs = self._get_kwargs()
        return session.resource(self.service_name or service_name, **resource_kwargs)


class AWSSettings(BaseModel):
    aws_access_key_id: str = Field(
        default="", description="AWS access key ID for authentication."
    )
    aws_secret_access_key: str = Field(
        default="", description="AWS secret access key for authentication."
    )
    region_name: str = Field(
        default=DEFAULT_REGION, description="Default AWS region for the client."
    )
    credentials_profile_name: str = Field(
        default="", description="Name of the AWS credentials profile to use."
    )
    endpoint_url: str = Field(
        default="",
        description="Custom endpoint URL, if using a non-standard AWS service endpoint.",
    )
    iam_role_assigned: bool = Field(
        default=False, description="Indicates if the required IAM role is assigned."
    )
    caller_identity: str = Field(
        default="",
        description="Amazon Resource Name (ARN) that uniquely identifies the caller based on the credentials provided.",
    )

    @classmethod
    def get_aws(cls, settings) -> Optional[Boto3Builder]:
        return Boto3Builder(
            profile_name=settings.get("credentials_profile_name"),
            aws_access_key_id=settings.get("aws_access_key_id"),
            aws_secret_access_key=settings.get("aws_secret_access_key"),
            endpoint_url=settings.get("endpoint_url"),
            iam_role_assigned=settings.get("iam_role_assigned"),
            region_name=settings.get("region_name", DEFAULT_REGION),
        )

    @classmethod
    def get_aws_client(cls, settings, service_name) -> Optional[Boto3Builder]:
        client_builder = cls.get_aws(settings)
        return client_builder.build_client(service_name)

    @classmethod
    def get_aws_resource(cls, settings, service_name) -> Optional[Boto3Builder]:
        resource_builder = cls.get_aws(settings)
        return resource_builder.build_resource(service_name)

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

        cls.set_identity(v.dict())

        return v

    @model_validator(mode="before")
    def set_identity(cls, v):
        client = cls.get_aws_client(v, service_name="sts")
        response = client.get_caller_identity()
        log.debug("AWS Caller Identity Response: %s", response)
        v["caller_identity"] = response["Arn"]

        return v

    class Config:
        extra = "forbid"
        anystr_strip_whitespace = True


@plugin
def settings_model():
    return AWSSettings
