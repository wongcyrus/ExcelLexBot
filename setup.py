import subprocess
import zipfile
from shutil import copyfile

import os


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

    deployment_steps = {
        'Package': True,
        'UploadTemplate': True,
        'UploadPackage': True
    }
    print("Copy Cloudformation and Excel")
    cloudformationFiles = ["lexbot", "codehook", "lex_builder"]
    list(map(lambda f: copyfile("./cloudformation/" + f + ".yaml", "./deployment/" + f + ".yaml"), cloudformationFiles))
    copyfile("./playground/MakeAppointmentChatBot.xlsx", "./deployment/MakeAppointmentChatBot.xlsx")

    print("Create Deployment package.")
    # Please change the virtual environment path.
    zip(['.\env\BotBuilder\Lib\site-packages/', './builder'], './deployment/lex_builder_function')
    zip(['.\env\BotBuilder\Lib\site-packages/', './lambda'], './deployment/lambda_function')

    # print("Upload Package")
    # subprocess.run(
    #     "aws s3 sync ./deployment/ s3://{0} --endpoint-url http://s3-accelerate.amazonaws.com".format(source_bucket),
    #     shell=True, check=True)

    print("Upload Cloudformation Template")
    list(map(lambda f: subprocess
             .run("aws s3 cp ./deployment/{0}.yaml s3://{1} --endpoint-url http://s3-accelerate.amazonaws.com"
                  .format(f, source_bucket), shell=True, check=True), cloudformationFiles))

    print("Transform Stack")

    # list(map(lambda f: subprocess.run(
    #     "aws cloudformation package --template-file ./deployment/{0}.yaml"
    #     " --output-template-file lexbot.json --s3-bucket {1}".format(f, source_bucket),
    #     shell=True, check=True), cloudformationFiles))

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
