import json
import os
import time

import requests

from BotBuilder import BotBuilder


def lambda_handler(event, context):
    print("Event: %s" % event)

    try:
        lambda_arn_prefix = context.invoked_function_arn.rsplit(':', 1)[0] + ":"
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        template_dir = os.path.join(dir_path, "lexjson")

        bot_builder = BotBuilder(None, template_dir, lambda_arn_prefix)

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
