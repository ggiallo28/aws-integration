from cat.mad_hatter.decorators import tool, hook, plugin
from .aws_cost_analysis import analyze_aws_costs
from . import Boto3
from cat.log import log
import json

iam_client = Boto3().get_client("iam")
sts_client = Boto3().get_client("sts")


def get_identity_info():
    identity_info = sts_client.get_caller_identity()
    arn_parts = identity_info["Arn"].split("/")
    identity_type = arn_parts[0].split(":")[-1]
    identity_name = arn_parts[-1]
    return identity_type, identity_name, identity_info["Arn"]


@tool(
    "AWS Self-Permission Identity Information",
    return_direct=True,
    examples=[
        "Who am I logged in as?",
        "What is my AWS IAM username?",
        "Am I using an IAM role or a user account?",
        "Show me my current AWS IAM identity.",
        "Retrieve the name of my AWS IAM user or role.",
    ],
)
def get_aws_identity_info(tool_input, cat):
    """
    Return the current user name or indicate if a role is being used.

    Use this tool when you need to find out the name of the current AWS IAM identity.
    This identity could be an IAM user or an IAM role. The function will return the name
    of the user if the identity is a user, or indicate that a role is being used along
    with the role name if the identity is a role.

    Note: This tool only works for retrieving identity information for the current authenticated
    AWS IAM user or role and does not take an identity as input.
    """
    try:
        identity_type, identity_name, identity_arn = get_identity_info()
        if identity_type in ("user"):
            return f"The username is {identity_name}."
        else:
            return f"I don't have a username, I am using an IAM role: {identity_arn}."
    except Exception as e:
        log.error(f"Error fetching user name: {e}")
        return "An error occurred while fetching the IAM identity information. Please check the AWS STS client configuration."


@tool(
    "AWS Self-Permission Policies Information",
    return_direct=True,
    examples=[
        "What permissions do I currently have?",
        "List the policies attached to my AWS IAM identity.",
        "What policies are associated with my IAM role?",
        "Show me the policies attached to my current IAM user or role.",
        "Retrieve the names of the policies attached to my AWS identity.",
    ],
)
def get_policies(tool_input, cat):
    """
    Return the permissions (policies attached to the current AWS IAM identity).

    Use this tool when you need to retrieve the list of policies attached to the current AWS IAM identity.
    This identity could be an IAM user or an IAM role. The function will return a list of policy names
    attached to the user or role.

    Note: This tool only works for retrieving permissions information for the current authenticated
    AWS IAM user or role and does not take an identity as input. It will fetch the policies attached to the
    identity that is making the request.
    """
    try:
        identity_type, identity_name, identity_arn = get_identity_info()
        if identity_type in ("user", "role", "assumed-role"):
            if identity_type == "user":
                attached_policies = iam_client.list_attached_user_policies(
                    UserName=identity_name
                )
            elif identity_type == "assumed-role":
                role_name = identity_arn.split("/")[-2]
                attached_policies = iam_client.list_attached_role_policies(
                    RoleName=role_name
                )
            else:
                attached_policies = iam_client.list_attached_role_policies(
                    RoleName=identity_name
                )
            policies = [
                policy["PolicyName"] for policy in attached_policies["AttachedPolicies"]
            ]
            return f"The attached policies are: {', '.join(policies)}."
        else:
            return f"Permissions are not applicable for identity type: {identity_type}"
    except Exception as e:
        log.error(f"Error fetching permissions: {e}")
        return "An error occurred while fetching the permissions. Please check the AWS IAM client configuration."


@tool(
    "AWS Self-Permission Account ID Retrieval",
    return_direct=True,
    examples=[
        "What is my AWS account ID?",
        "Show me my AWS account number.",
        "Which AWS account am I using?",
        "Retrieve my AWS account ID.",
        "Give me the account ID for my AWS account.",
    ],
)
def get_account_id(tool_input, cat):
    """
    Return the AWS account ID of the currently authenticated identity.

    Use this tool to retrieve the AWS account ID. The function returns the account ID as a string.

    Note: This tool only works for retrieving the account ID for the current authenticated AWS identity
    and does not take an identity as input.
    """
    try:
        response = sts_client.get_caller_identity()
        return f"The AWS account ID is: {response['Account']}."
    except Exception as e:
        log.error(f"Error fetching account ID: {e}")
        return "An error occurred while fetching the AWS account ID. Please check the AWS STS client configuration."


@tool(
    "AWS Self-Permission Identity Full Details",
    return_direct=True,
    examples=[
        "Provide all details about my AWS IAM identity.",
        "What are my IAM identity details?",
        "Show me everything about my current AWS IAM user or role.",
        "Retrieve full information about my IAM identity.",
        "Give me a complete overview of my AWS IAM user details.",
    ],
)
def get_identity_information(tool_input, cat):
    """
    Return all identity-related information.

    Use this tool when you need to gather comprehensive information about the current AWS IAM identity.
    This includes the account ID, ARN, identity type (user or role), identity name, permissions, and policies.

    Note: This tool only works for retrieving detailed information for the current authenticated AWS IAM user
    and does not take an identity as input.
    """
    try:
        caller_identity = sts_client.get_caller_identity()
        return f"""
Here are the Caller Identity Info:
```json
{json.dumps(caller_identity, indent=4)}
```
"""
    except Exception as e:
        log.error(f"Error fetching identity information: {e}")
        return "An error occurred while fetching the AWS IAM identity information. Please check the AWS STS client configuration."


@tool(
    "AWS Self-Permission Identity Type Detection",
    return_direct=True,
    examples=[
        "Am I logged in as a user or a role?",
        "What type of IAM identity am I using?",
        "Is my current identity an IAM user or a role?",
        "Determine if my IAM identity is a user or role.",
        "Check if I am using an IAM user or an IAM role.",
    ],
)
def get_identity_type(tool_input, cat):
    """
    Determine if the current identity is a user, role, or other type.

    Use this tool to understand whether the current AWS IAM identity is an IAM user, an IAM role, or another type of identity.
    This is useful for making decisions based on the type of IAM entity that is executing actions in your AWS environment.

    Note: This tool only works for detecting the identity type of the current authenticated AWS IAM user and does not take an identity as input.
    """
    try:
        identity_type, identity_name, identity_arn = get_identity_info()
        return f"The current identity is {identity_type}."
    except Exception as e:
        log.error(f"Error determining identity type: {e}")
        return "An error occurred while determining the IAM identity type. Please check the AWS STS client configuration."


@tool(
    "AWS Self-Permission IAM Groups Retrieval",
    return_direct=True,
    examples=[
        "Which groups do I belong to?",
        "List my AWS IAM groups.",
        "What groups is my IAM user associated with?",
        "Show me the IAM groups for my user.",
        "Retrieve the IAM groups for my AWS account.",
    ],
)
def get_groups(tool_input, cat):
    """
    Return the groups to which the current IAM user belongs.

    Use this tool to retrieve the list of groups for the current AWS IAM user.
    The function will return a list of group names associated with the user.

    Note: This tool only works for retrieving group memberships for the current authenticated
    AWS IAM user and does not take an identity as input.
    """
    try:
        identity_type, identity_name, identity_arn = get_identity_info()
        if identity_type == "user":
            user_groups = iam_client.list_groups_for_user(UserName=identity_name)
            groups = [group["GroupName"] for group in user_groups["Groups"]]
            return f"The current IAM user belongs to the following groups: {','.join(groups)}."
        else:
            return "Roles do not belong to IAM groups."
    except Exception as e:
        log.error(f"Error fetching groups: {e}")
        return "An error occurred while fetching the IAM groups. Please check the AWS IAM client configuration."


def get_permissions(tool_input, cat):
    try:
        identity_type, identity_name, identity_arn = get_identity_info()
        if identity_type in ["user", "role", "assumed-role"]:
            if identity_type == "user":
                inline_policies = iam_client.list_user_policies(UserName=identity_name)
            else:
                role_name = (
                    identity_name
                    if identity_type == "role"
                    else identity_arn.split("/")[-2]
                )
                inline_policies = iam_client.list_role_policies(RoleName=role_name)
            policies = {}
            for policy_name in inline_policies["PolicyNames"]:
                if identity_type == "user":
                    policy = iam_client.get_user_policy(
                        UserName=identity_name, PolicyName=policy_name
                    )
                else:
                    role_name = (
                        identity_name
                        if identity_type == "role"
                        else identity_arn.split("/")[-2]
                    )
                    policy = iam_client.get_role_policy(
                        RoleName=role_name, PolicyName=policy_name
                    )
                policies[policy_name] = policy["PolicyDocument"]
            if identity_type == "user":
                attached_policies = iam_client.list_attached_user_policies(
                    UserName=identity_name
                )
            else:
                role_name = (
                    identity_name
                    if identity_type == "role"
                    else identity_arn.split("/")[-2]
                )
                attached_policies = iam_client.list_attached_role_policies(
                    RoleName=role_name
                )
            for policy in attached_policies["AttachedPolicies"]:
                policy_arn = policy["PolicyArn"]
                policy_version = iam_client.get_policy(PolicyArn=policy_arn)["Policy"][
                    "DefaultVersionId"
                ]
                policy_document = iam_client.get_policy_version(
                    PolicyArn=policy_arn, VersionId=policy_version
                )["PolicyVersion"]["Document"]
                policies[policy["PolicyName"]] = policy_document
            return policies
    except Exception as e:
        log.error(f"Error fetching policies: {e}")
    return {}


@tool(
    "AWS Self-Permission Effective Permissions Retrieval",
    return_direct=True,
    examples=[
        "What are my effective permissions?",
        "List my combined AWS IAM permissions.",
        "Show me all permissions for my IAM user.",
        "Retrieve the effective permissions for my IAM user.",
        "Give me a summary of my IAM permissions.",
    ],
)
def get_effective_permissions(tool_input, cat):
    """
    Return the effective permissions for the current IAM user by combining all attached policies.

    Use this tool to retrieve the effective permissions for the current AWS IAM user.
    The function returns a dictionary of permissions derived from all attached policies.

    Note: This tool only works for retrieving effective permissions for the current authenticated
    AWS IAM user and does not take an identity as input.
    """
    try:
        policies = get_permissions(None, None)
        effective_permissions = {}

        def add_permission(permission_type, permission, resource, effect):
            if permission not in effective_permissions:
                effective_permissions[permission] = {"Allow": [], "Deny": []}
            if effect == "Allow":
                effective_permissions[permission]["Allow"].append(resource)
            elif effect == "Deny":
                effective_permissions[permission]["Deny"].append(resource)

        for policy_name, policy_document in policies.items():
            for statement in policy_document["Statement"]:
                effect = statement.get("Effect")

                actions = statement.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]

                not_actions = statement.get("NotAction", [])
                if isinstance(not_actions, str):
                    not_actions = [not_actions]

                resources = statement.get("Resource", [])
                if isinstance(resources, str):
                    resources = [resources]

                not_resources = statement.get("NotResource", [])
                if isinstance(not_resources, str):
                    not_resources = [not_resources]

                for action in actions:
                    for resource in resources:
                        add_permission("Action", action, resource, effect)

                for not_action in not_actions:
                    for resource in resources:
                        add_permission("NotAction", not_action, resource, effect)

                for action in actions:
                    for not_resource in not_resources:
                        add_permission("Action", action, not_resource, effect)

                for not_action in not_actions:
                    for not_resource in not_resources:
                        add_permission("NotAction", not_action, not_resource, effect)

        for permission, effects in effective_permissions.items():
            effects["Allow"] = sorted(list(set(effects["Allow"])))
            effects["Deny"] = sorted(list(set(effects["Deny"])))

        return f"""
The effective permissions for the current IAM identity are: 
```json
{json.dumps(effective_permissions, indent=4)}
```
"""
    except Exception as e:
        log.error(f"Error fetching effective permissions: {e}")
        return "An error occurred while fetching the effective permissions. Please check the AWS IAM client configuration."


@tool(
    "AWS Self-Permission MFA Status Check",
    return_direct=True,
    examples=[
        "Is MFA enabled for my IAM user?",
        "What is the MFA status for my current IAM user?",
        "Do I have MFA enabled on my IAM user account?",
        "Check the MFA status for my AWS IAM user.",
        "Am I using MFA for my AWS account?",
    ],
)
def get_mfa_status(tool_input, cat):
    """
    Return the MFA status of the current IAM user.

    Use this tool to check if Multi-Factor Authentication (MFA) is enabled for the current IAM user.
    The function will return the MFA status as a string.

    Note: This tool only works for retrieving MFA status for the current authenticated AWS IAM user
    and does not take an identity as input.
    """
    try:
        identity_type, identity_name, identity_arn = get_identity_info()
        if identity_type == "user":
            mfa_devices = iam_client.list_mfa_devices(UserName=identity_name)
            if mfa_devices["MFADevices"]:
                return "MFA is enabled."
            else:
                return "MFA is not enabled."
        else:
            return "MFA is applicable only for IAM users."
    except Exception as e:
        log.error(f"Error fetching MFA status: {e}")
        return "An error occurred while fetching the MFA status. Please check the AWS IAM client configuration."


@tool(
    "AWS Self-Permission Trust Policy Retrieval",
    return_direct=True,
    examples=[
        "Show me the trust policy for my IAM role.",
        "What is the trust policy for my current IAM role?",
        "List the trust policy details for my AWS IAM role.",
        "Retrieve the trust policy for my current AWS IAM role.",
        "Give me the trust policy document for my IAM role.",
    ],
)
def get_trust_policy(tool_input, cat):
    """
    Return the trust policy for the current IAM role.

    Use this tool to retrieve the trust policy document for the current AWS IAM role.
    The function returns the JSON trust policy document for the authenticated AWS IAM role.

    Note: This tool only works for retrieving trust policies for the current authenticated
    AWS IAM role and does not take an identity as input.
    """
    try:
        identity_type, identity_name, identity_arn = get_identity_info()
        if identity_type in ["role", "assumed-role"]:
            role_name = (
                identity_name
                if identity_type == "role"
                else identity_arn.split("/")[-2]
            )
            role = iam_client.get_role(RoleName=role_name)
            trust_policy = role["Role"]["AssumeRolePolicyDocument"]
            return f"""
The trust policies for the current IAM identity are: 
```json
{json.dumps(trust_policy, indent=4)}
```
"""
        else:
            return f"Trust policy is not applicable for identity type:  {identity_type}"
    except Exception as e:
        log.error(f"Error fetching trust policy: {e}")
        return "An error occurred while fetching the trust policy. Please check the AWS IAM client configuration."


@tool(
    "AWS Self-Permission Account Summary Retrieval",
    return_direct=True,
    examples=[
        "Show me my AWS account summary.",
        "What are the IAM statistics for my current AWS account?",
        "List the account summary details for my AWS account.",
        "Retrieve the IAM account summary for my AWS account.",
        "Give me an overview of the IAM statistics for my AWS account.",
    ],
)
def get_account_summary(tool_input, cat):
    """
    Return the account summary for the current AWS account.

    Use this tool to retrieve the account summary for the current AWS account.
    The function returns a summary of IAM user, group, role, and policy statistics.

    Note: This tool only works for retrieving account summaries for the current
    authenticated AWS account and does not take an identity as input.
    """
    try:
        account_summary = iam_client.get_account_summary()
        return f"""
The account summary is:
```json
{json.dumps(account_summary['SummaryMap'], indent=4)}
```
"""
    except Exception as e:
        log.error(f"Error fetching account summary: {e}")
        return "An error occurred while fetching the account summary. Please check the AWS IAM client configuration."


@tool(
    "AWS Cost Analysis",
    return_direct=True,
    examples=[
        "Analyze my AWS costs for the last 30 days",
        "Show me the AWS cost analysis for the past week",
        "What are my AWS expenses for the last 2 months?",
        "Get a breakdown of my AWS costs",
        "Provide an AWS cost analysis report",
    ],
)
def get_aws_cost_analysis(tool_input, cat):
    """
    Analyze AWS costs for the specified number of days.

    Use this tool when you need to get a detailed analysis of AWS costs for a specific time period.
    The function will return a dictionary containing cost analysis results.

    :param tool_input: The number of days to analyze (default: 30)
    :return: Dictionary containing cost analysis results
    """
    try:
        days = 30  # Default value
        if tool_input:
            days = int(tool_input)
        cost_analysis = analyze_aws_costs(days)
        return f"""
Here is the AWS cost analysis for the last {days} days:
```json
{cost_analysis}
```
"""
    except Exception as e:
        log.error(f"Error analyzing AWS costs: {e}")
        return "An error occurred while analyzing AWS costs. Please check the AWS configuration and try again."
