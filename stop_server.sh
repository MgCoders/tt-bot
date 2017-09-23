#/bin/bash
set -x
echo cd tt-bot-deploy en home
cd /home/ubuntu/tt-bot-deploy
docker-compose -f docker-compose.produccion.yml kill && docker-compose -f docker-compose.produccion.yml rm -f
if [ $? -eq 0 ]
then
  echo "Successfull"
  exit 0
else
  echo "Error" >&2
  exit 1
fi
