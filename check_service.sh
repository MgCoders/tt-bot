#/bin/bash
set -x
docker-compose --file=docker-compose.produccion.yml ps -q | xargs docker inspect -f '{{ .State.ExitCode }}' | while read code; do  
    if [ "$code" == "1" ]; then    
       exit -1
    fi
done
