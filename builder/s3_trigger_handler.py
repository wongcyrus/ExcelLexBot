import os
import zipfile
from shutil import copyfile
from time import sleep

import boto3
from boto3.s3.transfer import S3Transfer

from BotBuilder import BotBuilder

s3 = boto3.client('s3')
region = os.environ['AWS_REGION']
dynamodbAutoScaling = os.environ['DynamodbAutoScaling']
cloudformation = boto3.client('cloudformation')
tmp_folder = "/tmp/"


def lambda_handler(event, context):


    def get_object_information():
        record = event['Records'][0]
        return record['s3']['bucket']['name'], record['s3']['object']['key'], record["eventName"]

    source_bucket, xlsx_file_name, event_name = get_object_information()
    print(xlsx_file_name)

    stack_name = xlsx_file_name.lower().replace(".xlsx", "")
    aws_account = context.invoked_function_arn.split(":")[4]

    if event_name == "ObjectRemoved:Delete":
        print("Delete Excel Lex chatbot stack " + stack_name)
        response = cloudformation.delete_stack(
            StackName=stack_name
        )
        print(response)
    elif event_name == "ObjectCreated:Put":
        print("Create Excel Lex chatbot stack " + stack_name)
        create_excel_lex_chatbot_stack(aws_account, source_bucket, stack_name, xlsx_file_name)


def create_excel_lex_chatbot_stack(aws_account, source_bucket, stack_name, xlsx_file_name):
    base_path = os.environ['LAMBDA_TASK_ROOT']
    site_packages = os.path.join(base_path, '\env\BotBuilder\Lib\site-packages')
    change_set_name = stack_name + "ChangeSet"
    s3.download_file(source_bucket, xlsx_file_name, tmp_folder + xlsx_file_name)
    json_base_folder = os.path.join(tmp_folder, "json")
    json_output = os.path.join(tmp_folder, "json", "lexjson")
    deployment_output = os.path.join(tmp_folder, "deployment")



    assure_path_exists(json_base_folder)
    assure_path_exists(json_output)
    assure_path_exists(deployment_output)

    print("Generate Lex Json and cloudformation from Excel")
    xlsx_file_path = os.path.join(tmp_folder, xlsx_file_name)
    bot_builder = BotBuilder(xlsx_file_path, json_output,
                             "arn:aws:lambda:{0}:{1}:function:".format(region, aws_account))
    bot_builder.generate_cloudformation_resources()
    print("Copy Cloudformation")
    source = os.path.join(json_output, "lexbot.yaml")
    destination = os.path.join(deployment_output, stack_name + ".yaml")
    copyfile(source, destination)
    print("Create Deployment packages including Lex Json and dependencies")
    lex_builder_function_zip = os.path.join(deployment_output, stack_name)
    zip_dir([site_packages, base_path, json_base_folder], lex_builder_function_zip)
    print("Upload Package")
    upload_to_s3(source_bucket, os.path.join(deployment_output, stack_name + ".zip"))
    print("Upload Cloudformation Template")
    upload_to_s3(source_bucket, os.path.join(deployment_output, stack_name + ".yaml"))
    response = cloudformation.create_change_set(
        StackName=stack_name,
        TemplateURL='https://s3.amazonaws.com/{0}/code/{1}.yaml'.format(source_bucket, stack_name),
        Parameters=[
            {
                'ParameterKey': 'SourceBucket',
                'ParameterValue': source_bucket,
            },
            {
                'ParameterKey': 'DynamodbAutoScaling',
                'ParameterValue': dynamodbAutoScaling,
            }
        ],
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        ChangeSetName=change_set_name,
        ChangeSetType='CREATE'
    )
    print(response)
    execution_status = 'UNAVAILABLE'
    for i in range(1, 10):
        sleep(5)
        response = cloudformation.describe_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
        execution_status = response["ExecutionStatus"]
        if execution_status == "AVAILABLE":
            break
    if execution_status != "AVAILABLE":
        cloudformation.delete_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
        print("Cannot create change Set, so delete it!")
    else:
        response = cloudformation.execute_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
        print(response)


def assure_path_exists(path):
    newdir = os.path.dirname(path + "/")
    if os.path.exists(newdir):
        import shutil
        shutil.rmtree(newdir)
    os.makedirs(newdir)


def upload_to_s3(bucket: str, file_path_name: str):
    path, filename = os.path.split(file_path_name)
    transfer = S3Transfer(s3)
    transfer.upload_file(file_path_name, bucket, "code/" + filename)


def zip_dir(folders: list, dst):
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    for src in folders:
        abs_src = os.path.abspath(src)
        for dirname, subdirs, files in os.walk(src):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                # print('zipping %s as %s' % (os.path.join(dirname, filename), arcname))
                zf.write(absname, arcname)
    zf.close()
