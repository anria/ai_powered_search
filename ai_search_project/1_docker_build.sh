#docker compose -f docker.yaml up -d --build 

echo "Done with Dockers. Run Solr setups"

echo "CD .. "
cd ..
sleep 3
echo "Load Solr Configs"
sh _load_config_ai_law.sh

sleep 2
echo "Index Solr Data"
sh _index_ai_law.sh

echo "Ollama pull qwen3-embedding:0.6b"
# curl -X POST  "http://localhost:11434/api/pull" -H "Content-Type: application/json" -d '{"model": "qwen3-embedding:0.6b"}'
docker exec -it ollama-main ollama pull qwen3-embedding:0.6b
docker exec -it ollama-main ollama pull FableForge-AI/nexus-legal


echo "cd ai_search_project"
cd ai_search_project

echo "______ DONE ______"
# Exit with success (Standard convention)
exit 0


