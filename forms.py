from typing import Dict, List, Tuple, Optional, Any
from pydantic import BaseModel, Field
from contextlib import redirect_stdout

from cat.experimental.form import CatForm, CatFormState, form
from .aws_iam_tester import AwsIamTester
from tabulate import tabulate
from cat.log import log

import functools
from io import StringIO
from . import Boto3
import json
import requests
import re

iam_client = Boto3().get_client("iam")
sts_client = Boto3().get_client("sts")


class AwsIamPolicyTester:
    result = None
    status = None

    def __init__(
        self, debug: bool = False, sts_client=None, iam_client=None, s3_client=None
    ):
        self.debug = debug
        self.tester = AwsIamTester(
            debug=debug,
            sts_client=sts_client,
            iam_client=iam_client,
            s3_client=s3_client,
        )

    def _wrapper(func):
        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            self.result = ""
            stream = StringIO()
            with redirect_stdout(stream):
                self.status = func(self, *args, **kwargs)
            self.result = stream.getvalue()
            return self.result, self.status

        return inner

    def get_markdown(self):
        try:
            sources_separator, results_separator = " sources:", " results:"
            _, matching_sources, matching_results = self.result.split("INFO:")

            title_sources, array_sources = matching_sources.split(sources_separator)
            title_sources = title_sources.strip() + sources_separator
            array_sources = json.loads(array_sources)

            title_results, array_results = matching_results.split(results_separator)
            title_results = title_results.strip() + results_separator
            array_results = json.loads(array_results)

            def jsonIndentLimit(jsonString, indent, limit):
                regexPattern = re.compile(
                    f"\n({indent}){{{limit}}}(({indent})+|(?=(}}|])))"
                )
                return regexPattern.sub("", jsonString)

            json_results = jsonIndentLimit(json.dumps(array_results, indent=4), "  ", 8)
            json__sources = json.dumps(array_sources, indent=4)

            return f"""
{title_sources}
```json
{json__sources}
```

{title_results}
```json
{json_results}
```
"""
        except Exception as e:
            log.error(f"An error occured {e}")
            return self.result

    @_wrapper
    def check_access(
        self,
        action: str,
        resource: str = "*",
        user: Optional[str] = None,
        role: Optional[str] = None,
        json_output: bool = True,
    ) -> int:
        """
        Checks whether the provided IAM identity has permissions on the provided actions and resource.

        :return: 0 upon successful completion and allowed,
                 1 upon successful completion and not allowed,
                 2 upon failures
        """
        try:
            if user or role:
                allowed = self.tester.check_action(
                    user=user,
                    role=role,
                    action=action,
                    resource=resource,
                    json_output=json_output,
                )
            else:
                allowed = self.tester.check_access(
                    action=action,
                    resource=resource,
                    json_output=json_output,
                )
            return 0 if allowed else 1
        except Exception as e:
            print(f"Exception occurred: {e}")
            if self.debug:
                raise
            return 2

    @_wrapper
    def search_access(
        self, action: str, resource: str = "*", json_output: bool = True
    ) -> int:
        """
        Search which users and roles have access on the provided actions and resource.

        :return: 0 upon successful completion and allowed,
                 1 upon successful completion and not allowed,
                 2 upon failures
        """
        try:
            allowed = self.tester.check_access(
                action=action,
                resource=resource,
                json_output=json_output,
            )
            return 0 if allowed else 1
        except Exception as e:
            print(f"Exception occurred: {e}")
            if self.debug:
                raise
            return 2


class SearchAccess(BaseModel):
    action: str = Field(
        description="The specific operation or action to be validated, such as listing the contents of a storage bucket.",
    )
    resource: Optional[str] = Field(
        default="*",
        description="The unique identifier of the resource for which the action is being validated. Defaults to '*' indicating all resources.",
    )


@form
class SearchAccessForm(CatForm):
    description = (
        "Search which users and roles have access to the provided actions and resource. "
        "The IAM policy simulator evaluates the policies attached to all identities within "
        "your AWS account to determine who can perform specific actions on a given resource. "
        "This form is used to understand which users and roles are permitted to execute particular "
        "actions, helping to ensure that permissions are properly configured and identifying potential "
        "security risks by listing all identities that have access to critical resources."
    )
    model_class = SearchAccess
    start_examples = [
        "Find who can access this resource",
        "Search for IAM permissions",
        "Discover what actions are allowed",
        "Identify all users and roles with access to a resource",
        "List all roles that can perform this action",
    ]
    stop_examples = [
        "I'm done searching, no more information needed",
        "Stop the search, I have the details I wanted",
        "That's sufficient, I don't need to search further",
        "I have identified the necessary roles and users",
        "End the search for permissions",
    ]
    ask_confirm = True

    def submit(self, form_data):
        input_kwargs = {
            "action": form_data.get("action"),
            "resource": form_data.get("resource", "*"),
        }

        tester = AwsIamPolicyTester(
            debug=False, iam_client=iam_client, sts_client=sts_client
        )
        _ = tester.search_access(**input_kwargs)

        return {"output": tester.get_markdown()}


class CheckAccess(BaseModel):
    identity: str = Field(
        description="The unique identifier for the user, role, or assumed role whose permissions will be validated. This identifier follows a specific format indicating the type and account information.",
    )
    action: str = Field(
        description="The specific operation or action to be validated, such as listing the contents of a storage bucket.",
    )
    resource: Optional[str] = Field(
        default="*",
        description="The unique identifier of the resource for which the action is being validated. Defaults to '*' indicating all resources.",
    )


@form
class CheckAccessForm(CatForm):
    description = (
        "Checks whether the provided IAM identity has permissions on the provided actions and resource. "
        "The IAM policy simulator evaluates the policies attached to a specific IAM user or role to determine "
        "if they have the required permissions to perform certain actions on a given resource. "
        "This form is used when you need to verify the permissions of a specific identity, ensuring that the "
        "user or role has appropriate access rights and helping to troubleshoot permission issues or validate "
        "security configurations."
    )
    model_class = CheckAccess
    start_examples = [
        "Check the Role IAM permissions",
        "Verify the User access rights",
        "What can I do with this IAM user?",
        "I want to check if a specific action is allowed with an IAM Role",
        "Does this user have permission to perform an action?",
    ]
    stop_examples = [
        "That's enough, I don't need any more information",
        "I've got what I need, thanks",
        "Stop the access check, I'm done",
        "No further checks needed, thank you",
        "End the permission verification",
    ]
    ask_confirm = True

    def _classify_identity(self, identity: str) -> str:
        if re.match(r"^arn:aws:iam::\d{12}:user/[\w+=,.@-]+$", identity):
            return identity, None
        elif re.match(
            r"^arn:aws:iam::\d{12}:(role|assumed-role)/[\w+=,.@-]+(/[a-zA-Z_0-9+=,.@-]+)?$",
            identity,
        ):
            return None, identity
        else:
            raise ValueError("Invalid identity ARN format")

    def submit(self, form_data):
        identity = form_data.get("identity")
        user, role = self._classify_identity(identity)

        input_kwargs = {
            "user": user,
            "role": role,
            "action": form_data.get("action"),
            "resource": form_data.get("resource", "*"),
        }

        tester = AwsIamPolicyTester(
            debug=False, iam_client=iam_client, sts_client=sts_client
        )
        _ = tester.check_access(**input_kwargs)

        return {"output": tester.get_markdown()}


if __name__ == "__main__":
    tester = AwsIamPolicyTester(debug=False)
    _ = tester.check_access(action="s3:ListBucket", user="pippo.gallo")
    print(tester.get_markdown())
    _ = tester.search_access(action="s3:ListBucket")
    print(tester.get_markdown())
