import os
import zipfile
from shutil import copyfile
from time import sleep

import boto3
from boto3.s3.transfer import S3Transfer

from BotBuilder import BotBuilder

s3 = boto3.client('s3')
region = os.environ['AWS_REGION']


def lambda_handler(event, context):
    tmp_folder = "/tmp/"

    def get_bucket_key():
        for record in event['Records']:
            return record['s3']['bucket']['name'], record['s3']['object']['key']

    source_bucket, xlsx_file_name = get_bucket_key()
    print(xlsx_file_name)
    s3.download_file(source_bucket, xlsx_file_name, tmp_folder + xlsx_file_name)
    aws_account = context.invoked_function_arn.split(":")[4]

    # source_bucket = "howwhofeelinvideopackage"
    # aws_account = "894598711988"
    # region = "us-east-1"
    # Please change the virtual environment path.
    # site_packages = 'E:\Working\ExcelLexBot\env\BotBuilder\Lib\site-packages'
    # base_path = 'E:\\Working\\ExcelLexBot\\builder'
    # xlsx_file_name = "ChatBot.xlsx"

    base_path = os.environ['LAMBDA_TASK_ROOT']
    site_packages = os.path.join(base_path, '\env\BotBuilder\Lib\site-packages')

    stack_name = xlsx_file_name.lower().replace(".xlsx", "")
    change_set_name = stack_name + "ChangeSet"

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
    destination = os.path.join(deployment_output, "lexbot.yaml")
    copyfile(source, destination)

    print("Create Deployment packages including Lex Json and dependencies")
    lex_builder_function_zip = os.path.join(deployment_output, stack_name)
    zip_dir([site_packages, base_path, json_base_folder], lex_builder_function_zip)

    print("Upload Package")
    upload_to_s3(source_bucket, os.path.join(deployment_output, stack_name + ".zip"))

    print("Upload Cloudformation Template")
    upload_to_s3(source_bucket, os.path.join(deployment_output, "lexbot.yaml"))

    client = boto3.client('cloudformation')

    response = client.create_change_set(
        StackName=stack_name,
        TemplateURL='https://s3.amazonaws.com/{0}/lexbot.yaml'.format(source_bucket),
        Parameters=[
            {
                'ParameterKey': 'SourceBucket',
                'ParameterValue': source_bucket,
            }
        ],
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        ChangeSetName=change_set_name,
        ChangeSetType='CREATE'
    )
    print(response)

    for i in range(1, 10):
        sleep(5)
        response = client.describe_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
        execution_status = response["ExecutionStatus"]
        if execution_status == "AVAILABLE":
            break

    if execution_status != "AVAILABLE":
        client.delete_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
        print("Cannot create change Set, so delete it!")
    else:
        response = client.execute_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
        print(response)


def assure_path_exists(path):
    newdir = os.path.dirname(path + "/")
    if not os.path.exists(newdir):
        os.makedirs(newdir)


def upload_to_s3(bucket: str, file_path_name: str):
    path, filename = os.path.split(file_path_name)
    transfer = S3Transfer(s3)
    transfer.upload_file(file_path_name, bucket, filename)


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


if __name__ == '__main__':
    lambda_handler(None, None)
