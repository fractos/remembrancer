#!/bin/sh

if [ -z "$1" ]; then
  echo Usage:
  echo   register_key.sh <account-id> <access-key-id> <secret-access-key>
else
  echo Putting parameter into SSM/$REGION as $SSM_KEY_PREFIX$1

  aws ssm put-parameter \
    --region=$REGION \
    --name "$SSM_KEY_PREFIX$1" \
    --value '{"AWS_ACCESS_KEY_ID": "'$2'", "AWS_SECRET_ACCESS_KEY": "'$3'"}' \
    --type SecureString \
    --key-id alias/$KMS_KEY_ALIAS
fi
