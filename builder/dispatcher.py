import datetime
import json

import boto3
import os

region = os.environ['AWS_REGION']
lambda_client = boto3.client('lambda', region_name=region)
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    print("Event: %s" % event)
    response = lambda_client.list_functions(
        MaxItems=100
    )

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
        save_fulfillment(intent_name, event, slots)

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


def save_fulfillment(tablename: str, event, slots: dict):
    table = dynamodb.Table(tablename)
    data = slots
    data["userId"] = event["userId"]
    data["createAt"] = str(datetime.datetime.now())
    table.put_item(
        Item=data
    )


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
