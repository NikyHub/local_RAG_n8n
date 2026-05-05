#!/bin/bash
# Initialize Qdrant collection for Factory RAG
# Run after docker compose up -d

QDRANT_URL=${QDRANT_URL:-http://localhost:6333}

echo "Creating Qdrant collection: factory_knowledge..."

curl -s -X PUT "${QDRANT_URL}/collections/factory_knowledge" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1024,
      "distance": "Cosine"
    },
    "optimizers_config": {
      "default_segment_number": 2
    }
  }' | python3 -m json.tool 2>/dev/null || python -m json.tool 2>/dev/null || cat

echo ""
echo "Verifying collection..."
curl -s "${QDRANT_URL}/collections/factory_knowledge" | python3 -m json.tool 2>/dev/null || python -m json.tool 2>/dev/null || cat

echo ""
echo "Qdrant ready. Vector dimension: 1024 (bge-large-zh), Distance: Cosine"
