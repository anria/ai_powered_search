#!/bin/bash

for file in /Users/anria/ab_python/fix\ search/justia/data2/*.json; do
  curl -X POST -H 'Content-Type: application/json' \
       --data-binary @"$file" \
       "http://localhost:8983/solr/ai_law/update/json/docs"
done

# Send a single final commit call to write everything to disk
curl "http://localhost:8983/solr/ai_law/update?commit=true"
