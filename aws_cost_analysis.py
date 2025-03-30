import boto3
from datetime import datetime, timedelta
from cat.log import log


def get_aws_costs(
    start_date, end_date, client, granularity="DAILY", tag_key=None, tag_value=None
):
    """
    Retrieve AWS costs for a specified time period, optionally filtered by tag.

    :param start_date: Start date for the cost analysis (inclusive)
    :param end_date: End date for the cost analysis (exclusive)
    :param granularity: Granularity of the data (DAILY or MONTHLY)
    :param tag_key: The key of the tag to filter by (optional)
    :param tag_value: The value of the tag to filter by (optional)
    :return: Dictionary containing cost data
    """

    group_by = [{"Type": "DIMENSION", "Key": "SERVICE"}]
    filter_expr = {}

    if tag_key:
        group_by.append({"Type": "TAG", "Key": tag_key})

        if tag_value:
            filter_expr["Tags"] = {
                "Key": tag_key,
                "Values": [tag_value],
                "MatchOptions": ["EQUALS"],
            }
        else:
            filter_expr["Tags"] = {"Key": tag_key, "Values": [""]}

    if filter_expr:
        response = client.get_cost_and_usage(
            TimePeriod={
                "Start": start_date.strftime("%Y-%m-%d"),
                "End": end_date.strftime("%Y-%m-%d"),
            },
            Granularity=granularity,
            Metrics=["BlendedCost"],
            GroupBy=group_by,
            Filter=filter_expr,
        )
    else:
        response = client.get_cost_and_usage(
            TimePeriod={
                "Start": start_date.strftime("%Y-%m-%d"),
                "End": end_date.strftime("%Y-%m-%d"),
            },
            Granularity=granularity,
            Metrics=["BlendedCost"],
            GroupBy=group_by,
        )

    return response


def format_cost_data(response, tag_key=None):
    """
    Format the cost data for easier consumption.

    :param response: Response from the AWS Cost Explorer API
    :param tag_key: The key of the tag used for filtering (optional)
    :return: Formatted cost data
    """
    formatted_data = []
    for result in response["ResultsByTime"]:
        date = result["TimePeriod"]["Start"]
        for group in result["Groups"]:
            service = group["Keys"][0]
            cost = float(group["Metrics"]["BlendedCost"]["Amount"])
            item = {"date": date, "service": service, "cost": cost}
            if tag_key:
                item["tag"] = group["Keys"][1] if len(group["Keys"]) > 1 else "Untagged"
            formatted_data.append(item)
    return formatted_data


def get_total_cost(formatted_data):
    """
    Calculate the total cost from the formatted data.

    :param formatted_data: Formatted cost data
    :return: Total cost
    """
    return sum(item["cost"] for item in formatted_data)


def analyze_aws_costs(
    ce_client, days=30, granularity="DAILY", tag_key=None, tag_value=None
):
    """
    Analyze AWS costs for the specified number of days, optionally filtered by tag.

    :param days: Number of days to analyze (default: 30)
    :param tag_key: The key of the tag to filter by (optional)
    :param tag_value: The value of the tag to filter by (optional)
    :return: Dictionary containing cost analysis results
    """
    if granularity == "MONTHLY":
        days = 365

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    response = get_aws_costs(
        start_date,
        end_date,
        ce_client,
        granularity=granularity,
        tag_key=tag_key,
        tag_value=tag_value,
    )
    formatted_data = format_cost_data(response, tag_key)
    total_cost = get_total_cost(formatted_data)

    return {
        "total_cost": total_cost,
        "cost_by_service": formatted_data,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "tag_filter": f"{tag_key}:{tag_value}" if tag_key and tag_value else None,
    }
