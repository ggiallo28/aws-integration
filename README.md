# Amazon Web Services (AWS) Integration Plugin

[![awesome plugin](https://custom-icon-badges.demolab.com/static/v1?label=&message=awesome+plugin&color=383938&style=for-the-badge&logo=cheshire_cat_ai)](https://)
[![Awesome plugin](https://custom-icon-badges.demolab.com/static/v1?label=&message=Awesome+plugin&color=000000&style=for-the-badge&logo=cheshire_cat_ai)](https://)
[![awesome plugin](https://custom-icon-badges.demolab.com/static/v1?label=&message=awesome+plugin&color=F4F4F5&style=for-the-badge&logo=cheshire_cat_black)](https://)

This plugin integrates Amazon Web Services (AWS) functionality into the Cheshire Cat AI, providing tools for AWS IAM policy testing, access management, and cost analysis.

## Prerequisites

- Python 3.7 or higher
- Cheshire Cat AI platform
- AWS account with appropriate permissions
- `boto3` and `tabulate` Python libraries

## Features

- AWS IAM Policy Testing
- Access Management for AWS Resources
- Search for Users and Roles with Specific Permissions
- Check Access Rights for Specific IAM Identities
- AWS Cost Analysis with Tag Filtering

## Configuration

To use this plugin, you need to configure your AWS credentials. You can do this in one of the following ways:

1. IAM Role: Enable IAM role if your machine has the necessary permissions.
2. AWS Credentials Profile: Provide a profile name from your AWS credentials file.
3. Access Key and Secret: Directly provide your AWS access key ID and secret access key.

Configuration is done through the `AWSSettings` class in `aws_integration.py`. To set up the plugin:

1. Open the Cheshire Cat AI settings.
2. Navigate to the AWS Integration Plugin section.
3. Enter your AWS credentials or choose the authentication method.
4. Save the settings.

Make sure to keep your AWS credentials secure and never share them publicly.

### Docker Configuration

When running Cheshire Cat AI in a Docker environment, you need to mount your AWS credentials file to make it accessible to the container. Update your `docker-compose.yml` file with the following volume mount:

```yaml
volumes:
  - ./core:/app
  - $HOME/.aws/credentials:/root/.aws/credentials:ro
```

This mounts your local AWS credentials file into the Docker container in read-only mode.

### Authentication Methods

1. **Using AWS CLI Profile (Local Development)**
   - Ensure your AWS CLI is configured with the correct profile.
   - In the plugin settings, provide your profile name.
   - Mount your credentials as shown in the Docker configuration above.

2. **Using IAM Role (In AWS Environment)**
   - Enable the "IAM role assigned" option in the plugin settings.
   - Ensure your EC2 instance or ECS task has the necessary IAM role attached.

3. **Using Access Key and Secret Key (Universal)**
   - Provide your AWS Access Key ID and Secret Access Key in the plugin settings.
   - Alternatively, set the following environment variables:
     ```
     export AWS_ACCESS_KEY_ID=your_access_key
     export AWS_SECRET_ACCESS_KEY=your_secret_key
     export AWS_DEFAULT_REGION=your_preferred_region
     ```

For more information on configuring AWS credentials, refer to the [AWS CLI Environment Variables documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).

## Usage

### Search Access

Use the `SearchAccessForm` to find which users and roles have access to specific actions and resources.

Example:
```python
form_data = {
    "action": "s3:ListBucket",
    "resource": "*"
}
search_form = SearchAccessForm()
result = search_form.submit(form_data)
print(result["output"])
```

### Check Access

Use the `CheckAccessForm` to verify if a specific IAM identity has permissions for certain actions and resources.

Example:
```python
form_data = {
    "identity": "arn:aws:iam::123456789012:user/example-user",
    "action": "s3:ListBucket",
    "resource": "*"
}
check_form = CheckAccessForm()
result = check_form.submit(form_data)
print(result["output"])
```

### AWS Cost Analysis

Use the `get_aws_cost_analysis` tool to analyze AWS costs for a specified time period, with optional tag filtering.

Example usage:
```python
# Analyze costs for the last 30 days
result = get_aws_cost_analysis("30")

# Analyze costs for the last 7 days, filtered by the tag "project:website"
result = get_aws_cost_analysis("7 project:website")

print(result)
```

The tool accepts input in the format: `"<days> [tag_key:tag_value]"`. If no tag is specified, it will analyze all costs for the given period.

## Development

To start developing or modifying this plugin:

1. Clone this repository into your Cheshire Cat AI's `plugins` folder.
2. Install the required dependencies (boto3, tabulate).
3. Modify the Python files as needed.
4. Update the `plugin.json` file with any new version or configuration changes.

> **Important**
> A new release of your plugin is triggered every time you set a new `version` in the `plugin.json` file.
> Please, remember to set it correctly every time you want to release an update.

## Error Handling and Debugging

The AWS Integration Plugin includes error handling to manage common issues:

- If an AWS API call fails, the plugin will return an error message with details about the failure.
- For debugging purposes, you can enable debug mode in the `AwsIamPolicyTester` class by setting `debug=True` when initializing it.

If you encounter any issues:

1. Check your AWS credentials and ensure they have the necessary permissions.
2. Verify that your AWS region is set correctly in the plugin configuration.
3. Look for error messages in the Cheshire Cat AI logs.
4. If the issue persists, you can open an issue on the plugin's GitHub repository with a detailed description of the problem and any relevant error messages.
