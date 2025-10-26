#! /bin/bash

set -e
if [ -z "$REPO_URI" ]; then     
    SERVICE_NAME=$(yq '.parameters.ServiceName' aws/parameters.ecr.yaml | tr -d '"')    
    REPO_URI=$(aws cloudformation describe-stacks \
        --stack-name $SERVICE_NAME-ecr \
        --query "Stacks[0].Outputs[?ExportName=='${SERVICE_NAME}-ecr-uri'].OutputValue" \
        --output text)
    export REPO_URI
fi

REGISTRY_HOST=$(echo $REPO_URI | cut -d '/' -f1)

echo "Logging in to private ECR"
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${REGISTRY_HOST}

echo "Logging in to public ECR"
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws