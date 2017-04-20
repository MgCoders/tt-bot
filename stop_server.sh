#/bin/bash
set -x

ls $PWD 
docker-compose -f docker-compose.produccion.yml kill
