docker stop django-main django-container django-image

docker rm django-main
docker rm django-container
docker rm django-image

# STOP Sorl/zookeepers
docker stop solr-1000 solr-main zookeeper-main zookeeper solr-1000_solr_data solr-1000_zookeeper_data solr-1000_zookeeper_datalog

# REMOVE ALL solr logs
docker exec -it solr-main bash -c "rm -f /var/solr/logs/*.log*"
docker exec -it solr-1000 bash -c "rm -f /var/solr/logs/*.log*"

docker rm solr-main zookeeper-main 
docker rmi solr:10.0.0 zookeeper:3.9 solr-1000_solr_data solr-1000_zookeeper_data solr-1000_zookeeper_datalog

docker image prune  -a -f
docker volume prune -a -f
docker buildx prune -a -f
docker buildx history rm --all
docker system prune -a -f




# sudo sh -c 'truncate -s 0 $(docker inspect --format="{{.LogPath}}" <YOUR_SOLR_CONTAINER_NAME>)'
# REMOVE ALL Docker logs - hell yea!
# sudo sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log'
