export STACK_NAME=excellexbot
export AWS_DEFAULT_REGION=us-east-1
export REGION=$AWS_DEFAULT_REGION

echo "Deploy $STACK_NAME stack at $REGION region"

sourcebucket=excellexbotsource$STACK_NAME
aws s3 mb s3://$sourcebucket --region $REGION 
rm excellexbotpackage.yaml
sam package --template-file excellexbot.yaml --s3-bucket $sourcebucket --output-template-file excellexbotpackage.yaml

aws cloudformation deploy --stack-name $STACK_NAME --template-file excellexbotpackage.yaml \
--region $REGION --capabilities CAPABILITY_IAM \
--parameter-overrides DynamodbAutoScaling=false

rm codehookpackage.yaml                     
sam package --template-file codehook.yaml --s3-bucket $sourcebucket --output-template-file codehookpackage.yaml
aws cloudformation deploy --stack-name Codehook$STACK_NAME --template-file codehookpackage.yaml \
--region $REGION --capabilities CAPABILITY_IAM 
                        
