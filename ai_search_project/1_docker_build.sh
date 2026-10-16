docker compose -f docker.yaml up -d --build 


# INSTALL the Ollama models on the Ollama machine
# Nexus Legal
echo "Ollama pull FableForge-AI/nexus-legal"
docker exec -it ollama-main ollama pull FableForge-AI/nexus-legal
# Daniel's embedder
echo "Ollama pull hf.co/ggml-org/e5-small-v2-Q8_0-GGUF:Q8_0"
docker exec -it ollama-main ollama pull hf.co/ggml-org/e5-small-v2-Q8_0-GGUF:Q8_0
echo "granite3.1-moe:1b"
docker exec -it ollama-main ollama pull granite3.1-moe:1b
# Backup embedder
# echo "Ollama pull qwen3-embedding:0.6b"
# docker exec -it ollama-main ollama pull qwen3-embedding:0.6b

echo "Done with Dockers. Run Solr setups"

echo "CD .. "
cd ..
sleep 3
echo "Load Solr Configs"
sh _load_config_ai_law.sh

sleep 2
echo "Index Solr Data"
sh _index_ai_law.sh


echo "cd ai_search_project"
cd ai_search_project

echo "______ DONE ______"
# Exit with success (Standard convention)
exit 0


