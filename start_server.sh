#/bin/bash

echo cd tt-bot-deploy en home
cd /home/ubuntu/tt-bot-deploy
echo docker-compose up
$(aws ecr get-login --region us-east-1)
docker-compose -f docker-compose.produccion.yml pull --build
docker-compose -f docker-compose.produccion.yml up -d --build
