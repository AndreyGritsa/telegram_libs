import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="module", autouse=True)
def mock_pymongo_client():
    """Patch pymongo.mongo_client.MongoClient to return a mock client globally."""
    with patch('pymongo.mongo_client.MongoClient') as mock_mongo_client_class:
        mock_client_instance = MagicMock()
        mock_mongo_client_class.return_value = mock_client_instance
        yield mock_client_instance 