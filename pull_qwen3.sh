# curl -X POST  "http://10.5.0.5:11434/api/pull" -H "Content-Type: application/json" -d '{"model": "qwen3-embedding:0.6b"}'

echo "Pull qwen3-embedding"
docker exec -it ollama-main ollama pull qwen3-embedding:0.6b

echo "Pull FableForge-AI/nexus-legal"
docker exec -it ollama-main ollama pull FableForge-AI/nexus-legal

echo "exit Pull qwen3-embedding"
# Exit with success (Standard convention)
exit 0