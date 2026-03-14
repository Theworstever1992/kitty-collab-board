import pytest
from unittest.mock import MagicMock, patch
import backend.embeddings

def test_embedding_service_init():
    with patch('sentence_transformers.SentenceTransformer') as mock_st:
        svc = backend.embeddings.EmbeddingService(model_name="test-model")
        assert svc.model_name == "test-model"

        mock_st.return_value.encode.return_value = MagicMock(tolist=lambda: [0.1]*384)
        vec = svc.encode("hello")
        assert len(vec) == 384

def test_init_embedding_service():
    with patch('backend.embeddings.EmbeddingService') as mock_svc:
        backend.embeddings.init_embedding_service("test")
        assert backend.embeddings._service is not None

def test_get_embedding_service_error():
    backend.embeddings._service = None
    with pytest.raises(RuntimeError):
        backend.embeddings.get_embedding_service()
