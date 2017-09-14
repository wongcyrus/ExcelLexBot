import json

import boto3
import botocore
import requests
import time

from BotBuilder import BotBuilder


def lambda_handler(event, context):
    print("Event: %s" % event)

    try:
        bucket = event['ResourceProperties']['SourceBucket']
        key = event['ResourceProperties']['ExcelKey']

        s3 = boto3.resource('s3')
        try:
            s3.Bucket(bucket).download_file(key, '/tmp/bot.xlsx')
        except botocore.exceptions.ClientError as e:
            respond_cloudformation(event, "FAILED")

        lambda_arn_prefix = context.invoked_function_arn.rsplit(':', 1)[0] + ":"
        bot_builder = BotBuilder('/tmp/bot.xlsx', "/tmp", lambda_arn_prefix)

        if event['RequestType'] == 'Create':
            bot_builder.deploy_bot()
            respond_cloudformation(event, "SUCCESS")
        elif event['RequestType'] == 'Delete':
            bot_builder.undeploy_bot()
            respond_cloudformation(event, "SUCCESS")
        elif event['RequestType'] == 'Update':
            bot_builder.undeploy_bot()
            time.sleep(15)
            bot_builder.deploy_bot()
            respond_cloudformation(event, "SUCCESS")
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
            respond_cloudformation(event, "FAILED", e.message)
        else:
            print(e)
        respond_cloudformation(event, "FAILED")
    return


def respond_cloudformation(event, status, data=None):
    response_body = {
        'Status': status,
        'Reason': 'See the details in CloudWatch Log Stream',
        'PhysicalResourceId': 'Custom Lambda Function',
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': data
    }

    print('Response = ' + json.dumps(response_body))
    requests.put(event['ResponseURL'], data=json.dumps(response_body))
