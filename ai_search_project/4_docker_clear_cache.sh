# STOP it all
docker stop solr-main zookeeper-main ollama-main django-main django-app

docker rm django-main
docker rm solr-main
docker rm zookeeper-main
docker rm model-loader-1
docker rm ollama-main
docker rm django-image
docker rm solr:10.0.0
docker rm zookeeper:3.9
docker rm ollama/ollama:latest


# REMOVE ALL solr logs
docker exec -it solr-main bash -c "rm -f /var/solr/logs/*.log*"


docker image prune  -a -f
docker volume prune -a -f
docker builds prune -a -f
docker buildx history rm --all
docker system prune -a -f




# sudo sh -c 'truncate -s 0 $(docker inspect --format="{{.LogPath}}" <YOUR_SOLR_CONTAINER_NAME>)'
# REMOVE ALL Docker logs - hell yea!
# sudo sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log'
