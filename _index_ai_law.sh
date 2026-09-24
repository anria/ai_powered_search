#!/bin/bash

for file in data3/*.json; do
  curl -X POST -H 'Content-Type: application/json' \
       --data-binary @"$file" \
       "http://localhost:8983/solr/ai_law/update/json/docs"
done

sleep 1
# Send a single final hard commit call to write everything to disk
echo "Solr Commit for good measure"
curl "http://localhost:8983/solr/ai_law/update?commit=true"

echo "exit _index_ai_law.sh"
# Exit with success (Standard convention)
exit 0
