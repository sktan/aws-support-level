# MIT License
#
# Copyright (c) 2022 Steven Tan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import argparse
import inspect
from typing import TYPE_CHECKING, Any, List, Optional

import boto3
import requests

# https://awslabs.github.io/aws-crt-python/api/auth.html
from awscrt.auth import (
    AwsCredentialsProvider,
    AwsSignatureType,
    AwsSigningAlgorithm,
    AwsSigningConfig,
    aws_sign_request,
)

# https://awslabs.github.io/aws-crt-python/api/http.html#awscrt.http.HttpRequest
from awscrt.http import HttpRequest

if TYPE_CHECKING:
    from mypy_boto3_organizations import OrganizationsClient
    from mypy_boto3_sts import STSClient
else:
    STSClient = object
    OrganizationsClient = object


def list_org_accounts() -> List[dict[str, Any]]:
    """Gets a list of all active AWS accounts under an organization.

    Returns:
        A list of AWS Accounts under the current organization
    """
    organizations: OrganizationsClient = boto3.client("organizations")
    paginator = organizations.get_paginator("list_accounts")
    accounts = []
    for page in paginator.paginate():
        for account in page["Accounts"]:
            if account["Status"] != "ACTIVE":
                continue
            accounts.append(account)

    print(f"Retrieved a list of {len(accounts)} AWS accounts under the parent org.")

    return accounts


def assume_role(
    account_id: str,
    role_name: str,
    role_session_name: str,
) -> dict:
    """Assumes a role in a remote AWS account

    Args:
        account_id (str, int): The AWS account ID of the remote account
        role_name (str): The name of the role to assume
        role_session_name (str): The name of the role session

    Returns:
        An object with the credentials for the assumed role
    """
    sts: STSClient = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    print(f"Assuming role {role_arn}")
    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=role_session_name,
    )
    return response["Credentials"]


def get_support_plan(
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
) -> str:
    """Return the support plan for the current account.

    Args:
        aws_access_key_id (Optional[str], optional): AWS access key ID. Defaults to None.
        aws_secret_access_key (Optional[str], optional): AWS secret access key. Defaults to None.
        aws_session_token (Optional[str], optional): AWS session token. Defaults to None.

    Returns:
        str: The current support plan for this AWS account
    """

    credentials_provider = None
    if aws_access_key_id:
        credentials_provider = AwsCredentialsProvider.new_static(
            aws_access_key_id, aws_secret_access_key, aws_session_token
        )
    else:
        # Workaround for SSO support
        credentials = boto3.Session().get_credentials()
        credentials_provider = AwsCredentialsProvider.new_static(
            credentials.access_key, credentials.secret_key, credentials.token
        )

    http_request = HttpRequest(method="GET", path="/v1/getSupportPlan")
    http_request.headers.add("Host", "service.supportplans.us-east-2.api.aws")

    result: HttpRequest = aws_sign_request(
        http_request=http_request,
        signing_config=AwsSigningConfig(
            algorithm=AwsSigningAlgorithm.V4,
            signature_type=AwsSignatureType.HTTP_REQUEST_HEADERS,
            credentials_provider=credentials_provider,
            service="supportplans",
            region="us-east-2",
        ),
    ).result()

    response = requests.get(
        url="https://service.supportplans.us-east-2.api.aws/v1/getSupportPlan",
        headers=dict(result.headers),
    )

    if response.status_code == 403:
        raise Exception(response.json()["message"])

    return response.json()["supportPlan"].get("supportLevel", None)


def main():
    """The entrypoint of the CLI tool"""
    description = inspect.cleandoc(
        """
        A command line tool for fetching the support levels on your AWS Accounts

        Example usage:
        python3 support-level-direct.py --awsids 0123456789012,0123456789013 --role SupportRole
        python3 support-level-direct.py --org --role SupportRole
        python3 support-level-direct.py
        ------------------------
        https://github.com/sktan/aws-support-level
        """
    )

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description,
    )
    parser.add_argument("--awsids", default=None)
    parser.add_argument("--org", default=False, action="store_true")
    parser.add_argument("--role", default=None)
    args = parser.parse_args()

    if args.awsids and not args.role:
        raise Exception("You must specify a role to assume")
    if args.org and not args.role:
        raise Exception("You must specify a role to assume")
    if args.org and args.awsids:
        raise Exception("You cannot specify both --org and --awsids at the same time")

    if not args.role:
        support_level = get_support_plan()
        print(f"Your AWS support level is: {support_level}")
        return

    aws_ids = []

    if args.awsids:
        aws_ids = args.awsids.split(",")
    elif args.org:
        org_accounts = list_org_accounts()
        for account in org_accounts:
            aws_ids.append(account["Id"])

    output = []
    output.append("awsid,supportplan")
    for awsid in aws_ids:
        try:
            assume_role_result = assume_role(
                account_id=awsid,
                role_name=args.role,
                role_session_name="SupportPlanChecker",
            )
            support_level = get_support_plan(
                aws_access_key_id=assume_role_result["AccessKeyId"],
                aws_secret_access_key=assume_role_result["SecretAccessKey"],
                aws_session_token=assume_role_result["SessionToken"],
            )
            print(f"Account {awsid} has support level {support_level}")
            output.append(f"{awsid},{support_level}")
        except Exception as ex:
            print(f"Account {awsid} failed with error {ex}")
            output.append(f"{awsid},ERROR")

    with open("output.csv", "w", encoding="utf8") as file:
        file.write("\n".join(output))


if __name__ == "__main__":
    main()
