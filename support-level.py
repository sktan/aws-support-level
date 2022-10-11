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

from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_support import SupportClient
else:
    SupportClient = object


def get_support_severity_levels():
    client: SupportClient = boto3.client(
        service_name="support", region_name="us-east-1"
    )

    try:
        response = client.describe_severity_levels(language="en")

        severity_levels = []
        for severity_level in response["severityLevels"]:
            severity_levels.append(severity_level["code"])
    except client.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "SubscriptionRequiredException":
            return []
        raise err

    return severity_levels


__SUPPORT_LEVELS__ = {
    "critical": "ENTERPRISE",
    "urgent": "BUSINESS",
    "high": "BUSINESS",
    "normal": "DEVELOPER",
    "low": "DEVELOPER",
}


def main():
    """The entrypoint of the CLI tool"""
    support_levels = get_support_severity_levels()

    found = False
    for level, support_level in __SUPPORT_LEVELS__.items():
        if level in support_levels:
            found = True
            print(f"Your AWS support level is: {support_level}")
            break

    if not found:
        print("Your AWS support level is: BASIC")


if __name__ == "__main__":
    main()
