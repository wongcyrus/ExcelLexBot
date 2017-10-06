import os
import subprocess
import zipfile

import boto3


def zip_dir(folders: list, dst):
    zf = zipfile.ZipFile("%s.zip" % dst, "w", zipfile.ZIP_DEFLATED)
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
    delete_log_groups()

    source_bucket = "howwhofeelinvideopackage"
    aws_account = "894598711988"
    # Please change the virtual environment path.
    site_packages = '.\env\BotBuilder\Lib\site-packages/'

    print("Deploy Excel Lex Bot")
    print("Create Deployment packages including Lex Json and dependencies")
    zip_dir([site_packages, './builder'], './deployment/lex_builder_function')

    print("Deploy Excel Lex Builder")
    subprocess.run("aws s3 cp ./deployment/lex_builder_function.zip s3://{0} "
                   "--endpoint-url http://s3-accelerate.amazonaws.com"
                   .format(source_bucket))
    subprocess.run("aws s3 cp ./deployment/excellexbot.yaml s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com"
                   .format(source_bucket))
    subprocess.run(
        "aws cloudformation package --template-file ./deployment/excellexbot.yaml"
        " --output-template-file ./deployment/excellexbot_packaged.yaml --s3-bucket {0}".format(source_bucket),
        shell=True, check=True)
    subprocess.run(
        "aws cloudformation deploy --template-file ./deployment/excellexbot_packaged.yaml --stack-name excellexbot"
        " --parameter-overrides SourceBucket={0} ExcelBucketName={1}"
        " --capabilities CAPABILITY_IAM".format(source_bucket,"excellexbotdemo1"),
        shell=True, check=True)

    print("Deploy Code hook")
    zip_dir([site_packages, './codehook'], './deployment/codehook')

    subprocess.run("aws s3 cp ./deployment/codehook.zip s3://{0} "
                   "--endpoint-url http://s3-accelerate.amazonaws.com"
                   .format(source_bucket))

    subprocess.run("aws s3 cp ./deployment/codehook.yaml s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com"
                   .format(source_bucket))

    subprocess.run(
        "aws cloudformation package --template-file ./deployment/codehook.yaml"
        " --output-template-file ./deployment/codehook_packaged.yaml --s3-bucket {0}".format(source_bucket),
        shell=True, check=True)

    subprocess.run(
        "aws cloudformation deploy --template-file ./deployment/codehook_packaged.yaml --stack-name codehook"
        " --capabilities CAPABILITY_IAM".format(source_bucket),
        shell=True, check=True)

    print("Done")
