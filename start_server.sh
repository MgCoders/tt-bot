#/bin/bash

echo cd tt-bot-deploy en home
cd /home/ubuntu/tt-bot-deploy
cp ../.env ./
$(aws ecr get-login --region us-east-1)
docker-compose -f docker-compose.produccion.yml pull bot && docker-compose -f docker-compose.produccion.yml up -d --build bot
if [ $? -eq 0 ]
then
  echo "Successfull"
  exit 0
else
  echo "Error" >&2
  exit 1
fi
