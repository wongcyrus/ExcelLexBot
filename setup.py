import os
import subprocess
import zipfile
from shutil import copyfile

from BotBuilder import BotBuilder


def zip(folders: list, dst):
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
    source_bucket = "howwhofeelinvideopackage"
    aws_account = "894598711988"
    # Please change the virtual environment path.
    site_packages = '.\env\BotBuilder\Lib\site-packages/'

    print("Generate Lex Json from Excel")
    bot_builder = BotBuilder(os.path.join("./playground", "MakeAppointmentChatBot.xlsx"), "./output/lexjson",
                             "arn:aws:lambda:us-east-1:{0}:function:".format(aws_account))
    bot_builder.generate_json()

    print("Copy Cloudformation")
    copyfile("./cloudformation/lexbot.yaml", "./deployment/lexbot.yaml")

    print("Create Deployment packages including Lex Json and dependencies")
    zip([site_packages, './builder', './output'], './deployment/lex_builder_function')
    zip([site_packages, './lambda'], './deployment/lambda_function')

    print("Upload Package")
    subprocess.run(
        "aws s3 sync ./deployment/ s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com".format(source_bucket),
        shell=True, check=True)

    print("Upload Cloudformation Template")
    subprocess.run("aws s3 cp ./deployment/lexbot.yaml s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com"
                   .format(source_bucket))

    print("Transform Stack")
    subprocess.run(
        "aws cloudformation package --template-file ./deployment/lexbot.yaml"
        " --output-template-file lexbot.json --s3-bucket {0}".format(source_bucket),
        shell=True, check=True)

    print("Create Stack")
    subprocess.run(
        "aws cloudformation deploy --template-file lexbot.json --stack-name lex"
        " --capabilities CAPABILITY_IAM".format(source_bucket),
        shell=True, check=True)

    print("Done")
