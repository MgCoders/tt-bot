#/bin/bash
set -x

echo cd tt-bot-deploy en home
cd /home/ubuntu/tt-bot-deploy
echo docker-compose kill
docker-compose -f docker-compose.produccion.yml kill
