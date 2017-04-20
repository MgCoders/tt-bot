#/bin/bash

echo cd tt-bot-deploy en home
cd /home/ubuntu/tt-bot-deploy
echo docker-compose up
docker-compose -f docker-compose.produccion.yml up -d --build bot
