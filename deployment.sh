STACK_NAME=excellexbot
REGION=us-east-1

echo "Deploy $STACK_NAME stack"

sourcebucket=cywongexcellexbot
excelBuckketName=cywongexcellexsource
aws s3 mb s3://$sourcebucket --region $REGION
cp -rf builder/* venv/lib/python3.6/dist-packages
rm package.yaml
sam package --template-file deployment/excellexbot.yaml --s3-bucket $sourcebucket --output-template-file package.yaml

aws cloudformation deploy --stack-name $STACK_NAME --template-file package.yaml \
--region $REGION --capabilities CAPABILITY_IAM \
--parameter-overrides \
    ExcelBucketName=$excelBuckketName \
    DynamodbAutoScaling=false 
