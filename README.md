# AWS Support Level Tool

This tool helps you identify the AWS support level of the following:

- Your current AWS account
- A list of AWS Account IDs
- All the accounts in your AWS organisation

I'm using Python 3.10 to develop and run this, but anything python 3.7 and above should work as long as you have the following Python libraries installed:

- boto3
- awscrt
- requests

If you are interested in learning more about why this was built and how I found the SupportPlans API, feel free to check out my [blog post](https://www.sktan.com/blog/post/7-determining-your-aws-support-level-via-the-supportplans-api).

## Usage - support-level-direct.py (Undocumented SupportPlans API)

This version of the tool uses an undocumented SupportPlans API provided by AWS to show you your current subscription in the "Change Support Plans" page.

You will notice that I am using the us-east-2 region and that is intended. Even though the Support Console runs in the us-east-1 region, this API is only available in us-east-2 from what I've found.

```console
# Install the pipenv requirements and open a shell
sktan ➜ /workspaces/aws-support-level (master ✗) $ pipenv install
sktan ➜ /workspaces/aws-support-level (master ✗) $ pipenv shell

# Run the command against the entire organisation (you will need to run this from a role that has access to the organisation parent account)
(aws-support-level) sktan ➜ /workspaces/aws-support-level (master ✗) $ python support-level-direct.py --org --role sktan-org-support
Retrieved a list of 14 AWS accounts under the parent org.
Assuming role arn:aws:iam::0123456789012:role/sktan-org-support
Account 0123456789012 has support level ENTERPRISE
Assuming role arn:aws:iam::0123456789013:role/sktan-org-support
Account 0123456789013 has support level BUSINESS
Assuming role arn:aws:iam::0123456789014:role/sktan-org-support
Account 0123456789014 failed with error An error occurred (AccessDenied) when calling the AssumeRole operation: User: arn:aws:sts::0123456789014:assumed-role/AWSReservedSSO_AdministratorAccess_asdf1234/sktan is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::0123456789014:role/sktan-org-support
Assuming role arn:aws:iam::0123456789015:role/sktan-org-support
Account 0123456789015 has support level BASIC

# Run the command against a list of AWS Account Ids
(aws-support-level) sktan ➜ /workspaces/aws-support-level (master ✗) $ python support-level.py --awsids 0123456789012,0123456789013 --role sktan-org-support
Assuming role arn:aws:iam::0123456789012:role/sktan-org-support
Account 0123456789012 has support level ENTERPRISE
Assuming role arn:aws:iam::0123456789013:role/sktan-org-support
Account 0123456789013 has support level BUSINESS

# Run the command against the current AWS account
(aws-support-level) sktan ➜ /workspaces/aws-support-level (master ✗) $ python support-level.py
Your AWS support level is: BASIC
```

### CSV Output

When running the command, you will get an ouptut of the tool's actions and which accounts it's currently performing API actions against. Once this is completed, it will spit out an `output.csv` file which looks like:

```csv
awsid,supportplan
0123456789012,ENTERPRISE
0123456789013,BUSINESS
0123456789014,ERROR
0123456789015,BASIC
```

NOTE: If running against a singlular account, you will not receive any CSV file output.

### Required IAM Permissions - support-level-direct.py

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "supportplans:GetSupportPlan",
            "Resource": "*"
        }
    ]
}
```

## Usage - support-level.py (Get Severity Levels)

This method isn't as feature-rich and only supports the current account you're authenticated to. It currently only provides you a guesstimate of your AWS support level based on the information in the [Choosing a Severity](https://docs.aws.amazon.com/awssupport/latest/user/case-management.html#choosing-severity) section of the AWS Support User Guide.

```
# Run this against the current account
(aws-support-level) sktan ➜ /workspaces/aws-support-level (master ✗) $ python support-level.py
Your AWS support level is: BASIC
```

### Required IAM Permissions - support-level.py

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "support:DescribeSeverityLevels",
            "Resource": "*"
        }
    ]
}
```
