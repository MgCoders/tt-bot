#/bin/bash
ls $PWD 
docker-compose -f docker-compose.produccion.yml kill
docker-compose -f docker-compose.produccion.yml up -d
