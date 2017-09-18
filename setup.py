import os
import subprocess
import zipfile
from shutil import copyfile

import boto3

from BotBuilder import BotBuilder


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


def delete_log_groups():
    client = boto3.client('logs')
    response = client.describe_log_groups()
    for l in response['logGroups']:
        print(l)
        client.delete_log_group(logGroupName=l['logGroupName'])


if __name__ == '__main__':
    source_bucket = "howwhofeelinvideopackage"
    aws_account = "894598711988"
    # Please change the virtual environment path.
    site_packages = '.\env\BotBuilder\Lib\site-packages/'

    print("Generate Lex Json from Excel")
    bot_builder = BotBuilder(os.path.join("./playground", "ChatBot.xlsx"), "./output/lexjson",
                             "arn:aws:lambda:us-east-1:{0}:function:".format(aws_account))
    bot_builder.generate_cloudformation_resources()

    print("Copy Cloudformation")
    copyfile("./output/lexjson/lexbot.yaml", "./deployment/lexbot.yaml")
    copyfile("./codehook/codehook.yaml", "./deployment/codehook.yaml")

    print("Create Deployment packages including Lex Json and dependencies")
    zip_dir([site_packages, './builder', './output'], './deployment/lex_builder_function')
    zip_dir([site_packages, './codehook'], './deployment/lambda_function')

    print("Upload Package")
    subprocess.run(
        "aws s3 sync ./deployment/ s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com".format(source_bucket),
        shell=True, check=True)

    print("Upload Cloudformation Template")
    subprocess.run("aws s3 cp ./deployment/lexbot.yaml s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com"
                   .format(source_bucket))
    subprocess.run("aws s3 cp ./deployment/codehook.yaml s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com"
                   .format(source_bucket))

    print("Delete Old Log Group")
    delete_log_groups()

    print("Transform Stack")
    subprocess.run(
        "aws cloudformation package --template-file ./deployment/lexbot.yaml"
        " --output-template-file ./deployment/lexbot_packaged.yaml --s3-bucket {0}".format(source_bucket),
        shell=True, check=True)

    subprocess.run(
        "aws cloudformation package --template-file ./deployment/codehook.yaml"
        " --output-template-file ./deployment/codehook_packaged.yaml --s3-bucket {0}".format(source_bucket),
        shell=True, check=True)

    print("Create Stack")
    subprocess.run(
        "aws cloudformation deploy --template-file ./deployment/lexbot_packaged.yaml --stack-name lex"
        " --capabilities CAPABILITY_IAM".format(source_bucket),
        shell=True, check=True)

    subprocess.run(
        "aws cloudformation deploy --template-file ./deployment/codehook_packaged.yaml --stack-name codehook"
        " --capabilities CAPABILITY_IAM".format(source_bucket),
        shell=True, check=True)

    print("Done")
