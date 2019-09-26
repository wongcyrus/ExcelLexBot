import boto3


def delete_log_groups():
    client = boto3.client('logs')
    response = client.describe_log_groups()
    for l in response['logGroups']:
        if "LexBuilderCustomReseo" in l['logGroupName']:
            print(l)
            client.delete_log_group(logGroupName=l['logGroupName'])


if __name__ == '__main__':
    delete_log_groups()
