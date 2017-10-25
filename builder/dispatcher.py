import datetime
import json
import os

import boto3
from botocore.exceptions import ClientError

region = os.environ['AWS_REGION']
lambda_client = boto3.client('lambda', region_name=region)
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')


def lambda_handler(event, context):
    print("Event: %s" % event)
    response = lambda_client.list_functions(
        MaxItems=100
    )

    aws_account_id = context.invoked_function_arn.split(":")[4]

    function_set = set(map(lambda f: f.get("FunctionName"), response.get("Functions")))
    print(function_set)

    source = event['invocationSource']
    output_session_attributes = event['sessionAttributes'] if event['sessionAttributes'] is not None else {}
    slots = event['currentIntent']['slots']

    intent_name = event['currentIntent']['name']
    fulfillment = intent_name + "_fulfillmentActivity"
    dialog = intent_name + "_dialogCodeHook"
    code_hooks = [intent_name, fulfillment, dialog]

    if source == 'FulfillmentCodeHook':
        save_fulfillment(intent_name, event)
        publish_to_sns(intent_name, event, aws_account_id)

    responses = list(map(lambda x: call_lambda(event, x, function_set), code_hooks))
    if all(v is None for v in responses):
        if source == 'DialogCodeHook':
            return delegate(output_session_attributes, slots)
        elif source == 'FulfillmentCodeHook':
            return close(
                output_session_attributes,
                'Fulfilled',
                {
                    'contentType': 'PlainText',
                    'content': 'Okay, thank you!'
                }
            )
    else:
        # get Code Hook response.
        response = [x for x in responses if x is not None].pop()
        print(responses)
        return response


def call_lambda(event, function_name, function_set):
    if function_name in function_set:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        data = json.loads(response['Payload'].read().decode("utf-8"))
        print(data)
        return data
    else:
        return None


def save_fulfillment(table_name: str, event):
    table = dynamodb.Table(table_name.replace("_", ""))
    data = get_save_data(event)
    table.put_item(
        Item=data
    )


def publish_to_sns(intend: str, event: dict, aws_account_id: str):
    arn = "arn:aws:sns:{0}:{1}:{2}SNSTopic".format(region, aws_account_id, intend.replace("_", ""))
    data = get_save_data(event)
    data = json.dumps({"default": ''.join('{} : {} \n'.format(key, val) for key, val in data.items())})
    try:
        sns.publish(
            TopicArn=arn,
            Message=data,
            Subject="New message from " + intend,
            MessageStructure='json'
        )
        print("sns:\n" + data)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NotFoundException':
            print("No Topic for " + intend)
        else:
            print("Unexpected error: %s" % e)


def get_save_data(event):
    data = event['currentIntent']['slots'].copy()
    data["createAt"] = str(datetime.datetime.now())
    data["userId"] = event["userId"]
    data["sessionAttributes"] = event['sessionAttributes'].copy()
    return data


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def close(session_attributes, fulfillment_state, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
