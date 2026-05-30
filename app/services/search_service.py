from elasticsearch import Elasticsearch
from app.core.config import settings

es = Elasticsearch([settings.ELASTICSEARCH_URL])

def create_index_if_not_exists():
    """
    Creates the Elasticsearch index mapping for hybrid search.
    Defines the dense_vector field for ResNet50 embeddings (2048 dimensions).
    """
    index_name = getattr(settings, "ELASTICSEARCH_INDEX", "pins")
    
    try:
        if not es.indices.exists(index=index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "pin_id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "english"},
                        "description": {"type": "text", "analyzer": "english"},
                        "image_vector": {
                            "type": "dense_vector",
                            "dims": 2048
                        }
                    }
                }
            }
            es.indices.create(index=index_name, body=mapping)
            print(f"Successfully created Elasticsearch index schema: {index_name}")
    except Exception as e:
        print(f"Failed to create Elasticsearch index (is ES running?): {e}")

create_index_if_not_exists()

def index_pin(pin_id, title: str, description: str, image_vector: list):
    """
    Index a pin in Elasticsearch with text for BM25 and vector for semantic search.
    pin_id is a UUID string.
    """
    index_name = getattr(settings, "ELASTICSEARCH_INDEX", "pins")
    doc = {
        "pin_id": str(pin_id),
        "title": title or "",
        "description": description or "",
        "image_vector": image_vector
    }
    try:
        es.index(index=index_name, id=str(pin_id), document=doc)
    except Exception as e:
        print(f"Failed to index in ES: {e}")

def search_pins(query: str = None, query_vector: list = None, size=10):
    """
    Hybrid search combining BM25 keyword matching and vector similarity.
    Returns list of pin_id strings (UUIDs).
    """
    index_name = getattr(settings, "ELASTICSEARCH_INDEX", "pins")
    es_query = {
        "size": size,
        "query": {
            "bool": {
                "must": []
            }
        }
    }
    
    if query:
        es_query["query"]["bool"]["must"].append({
            "multi_match": {
                "query": query,
                "fields": ["title", "description"]
            }
        })
        
    if query_vector:
        vector_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'image_vector') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
        es_query["query"]["bool"]["must"].append(vector_query)
        
    try:
        res = es.search(index=index_name, body=es_query)
        return [hit["_source"]["pin_id"] for hit in res["hits"]["hits"]]
    except Exception as e:
        print(f"ES search failed: {e}")
        return []