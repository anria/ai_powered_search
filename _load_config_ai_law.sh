#!/bin/bash

echo "zip ai_law"
cd ai_law
rm -f ai_law.zip
zip -r ai_law.zip .

echo "upload ai_law configs to Solr"
curl -X PUT --header "Content-Type:application/octet-stream" --data-binary @ai_law.zip  "http://localhost:8983/api/configsets/ai_law?overwrite=true"

sleep 3
echo "create ai_law core"
curl -X POST "http://localhost:8983/solr/admin/collections?action=CREATE&name=ai_law&numShards=1&replicationFactor=1&collection.configName=ai_law"

sleep 3
echo "reload ai_law core"
curl -X POST 'http://localhost:8983/solr/admin/collections?action=RELOAD&name=ai_law'


echo "exit _load_config_ai_law"
# Exit with success (Standard convention)
exit 0