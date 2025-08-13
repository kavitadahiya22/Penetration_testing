"""
OpenSearch client and query utilities for testing
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from opensearchpy import AsyncOpenSearch, OpenSearch
from datetime import datetime, timezone


class OpenSearchClient:
    """Async OpenSearch client for testing"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        scheme: str = "http",
        username: str = "",
        password: str = "",
        verify_certs: bool = False,
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.username = username
        self.password = password
        self.verify_certs = verify_certs
        self.timeout = timeout
        self.client = None
    
    def _get_client(self):
        """Get or create OpenSearch client"""
        if not self.client:
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            self.client = AsyncOpenSearch(
                hosts=[{"host": self.host, "port": self.port}],
                http_auth=auth,
                use_ssl=self.scheme == "https",
                verify_certs=self.verify_certs,
                timeout=self.timeout,
                http_compress=True,
                max_retries=3,
                retry_on_timeout=True
            )
        return self.client
    
    async def close(self):
        """Close the client"""
        if self.client:
            await self.client.close()
    
    async def cluster_health(self) -> bool:
        """Check cluster health"""
        try:
            client = self._get_client()
            health = await client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception:
            return False
    
    async def index_exists(self, index_name: str) -> bool:
        """Check if index exists"""
        try:
            client = self._get_client()
            return await client.indices.exists(index=index_name)
        except Exception:
            return False
    
    async def create_index(self, index_name: str, mapping: Optional[Dict] = None) -> bool:
        """Create index with optional mapping"""
        try:
            client = self._get_client()
            
            body = {}
            if mapping:
                body["mappings"] = mapping
            
            await client.indices.create(index=index_name, body=body)
            return True
        except Exception as e:
            print(f"Failed to create index {index_name}: {e}")
            return False
    
    async def delete_index(self, index_name: str) -> bool:
        """Delete index"""
        try:
            client = self._get_client()
            await client.indices.delete(index=index_name)
            return True
        except Exception:
            return False
    
    async def search(
        self,
        index: str,
        query: Dict[str, Any],
        size: int = 100,
        sort: Optional[List[Dict]] = None,
        source: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search documents"""
        client = self._get_client()
        
        body = {"query": query, "size": size}
        
        if sort:
            body["sort"] = sort
        
        if source:
            body["_source"] = source
        
        return await client.search(index=index, body=body)
    
    async def get_document(self, index: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            client = self._get_client()
            response = await client.get(index=index, id=doc_id)
            return response["_source"]
        except Exception:
            return None
    
    async def index_document(
        self,
        index: str,
        document: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> str:
        """Index a document"""
        client = self._get_client()
        
        if doc_id:
            await client.index(index=index, id=doc_id, body=document)
            return doc_id
        else:
            response = await client.index(index=index, body=document)
            return response["_id"]
    
    async def delete_document(self, index: str, doc_id: str) -> bool:
        """Delete document by ID"""
        try:
            client = self._get_client()
            await client.delete(index=index, id=doc_id)
            return True
        except Exception:
            return False
    
    async def count_documents(self, index: str, query: Optional[Dict] = None) -> int:
        """Count documents matching query"""
        client = self._get_client()
        
        body = {}
        if query:
            body["query"] = query
        
        response = await client.count(index=index, body=body)
        return response["count"]
    
    async def refresh_index(self, index: str) -> bool:
        """Refresh index to make documents searchable"""
        try:
            client = self._get_client()
            await client.indices.refresh(index=index)
            return True
        except Exception:
            return False


class OpenSearchQueries:
    """Common OpenSearch queries for testing"""
    
    @staticmethod
    def match_all() -> Dict[str, Any]:
        """Match all documents query"""
        return {"match_all": {}}
    
    @staticmethod
    def term_query(field: str, value: str) -> Dict[str, Any]:
        """Exact term query"""
        return {"term": {field: value}}
    
    @staticmethod
    def terms_query(field: str, values: List[str]) -> Dict[str, Any]:
        """Multiple terms query"""
        return {"terms": {field: values}}
    
    @staticmethod
    def range_query(field: str, gte: Any = None, lte: Any = None, gt: Any = None, lt: Any = None) -> Dict[str, Any]:
        """Range query"""
        range_params = {}
        if gte is not None:
            range_params["gte"] = gte
        if lte is not None:
            range_params["lte"] = lte
        if gt is not None:
            range_params["gt"] = gt
        if lt is not None:
            range_params["lt"] = lt
        
        return {"range": {field: range_params}}
    
    @staticmethod
    def bool_query(
        must: Optional[List[Dict]] = None,
        should: Optional[List[Dict]] = None,
        must_not: Optional[List[Dict]] = None,
        filter: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Boolean query"""
        bool_params = {}
        
        if must:
            bool_params["must"] = must
        if should:
            bool_params["should"] = should
        if must_not:
            bool_params["must_not"] = must_not
        if filter:
            bool_params["filter"] = filter
        
        return {"bool": bool_params}
    
    @staticmethod
    def exists_query(field: str) -> Dict[str, Any]:
        """Field exists query"""
        return {"exists": {"field": field}}
    
    @staticmethod
    def wildcard_query(field: str, pattern: str) -> Dict[str, Any]:
        """Wildcard query"""
        return {"wildcard": {field: pattern}}
    
    @staticmethod
    def time_range_query(field: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Time range query"""
        return OpenSearchQueries.range_query(field, gte=start_time, lte=end_time)


class TestDataHelper:
    """Helper class for managing test data in OpenSearch"""
    
    def __init__(self, client: OpenSearchClient):
        self.client = client
        self.created_indices = set()
        self.created_documents = []
    
    async def setup_test_indices(self, indices_config: Dict[str, Dict]) -> bool:
        """Setup test indices with mappings"""
        try:
            for index_name, config in indices_config.items():
                mapping = config.get("mapping")
                if not await self.client.index_exists(index_name):
                    await self.client.create_index(index_name, mapping)
                    self.created_indices.add(index_name)
                    print(f"Created test index: {index_name}")
                
                # Refresh index to ensure it's ready
                await self.client.refresh_index(index_name)
            
            return True
        except Exception as e:
            print(f"Failed to setup test indices: {e}")
            return False
    
    async def cleanup_test_data(self) -> None:
        """Clean up created test data"""
        # Delete created documents
        for index, doc_id in self.created_documents:
            try:
                await self.client.delete_document(index, doc_id)
            except Exception:
                pass
        
        # Optionally delete created indices (commented out for safety)
        # for index_name in self.created_indices:
        #     try:
        #         await self.client.delete_index(index_name)
        #     except Exception:
        #         pass
        
        self.created_documents.clear()
        # self.created_indices.clear()
    
    async def wait_for_document(
        self,
        index: str,
        query: Dict[str, Any],
        timeout: int = 30,
        interval: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Wait for a document to appear in OpenSearch"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                response = await self.client.search(index, query, size=1)
                if response["hits"]["total"]["value"] > 0:
                    return response["hits"]["hits"][0]["_source"]
            except Exception:
                pass
            
            await asyncio.sleep(interval)
        
        return None
    
    async def wait_for_document_count(
        self,
        index: str,
        expected_count: int,
        query: Optional[Dict] = None,
        timeout: int = 30,
        interval: int = 1
    ) -> bool:
        """Wait for specific document count"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                count = await self.client.count_documents(index, query)
                if count >= expected_count:
                    return True
            except Exception:
                pass
            
            await asyncio.sleep(interval)
        
        return False


# Common index mappings for testing
PLANNER_INDEX_MAPPING = {
    "properties": {
        "plan_id": {"type": "keyword"},
        "tenant_id": {"type": "keyword"},
        "created_at": {"type": "date"},
        "model_provider": {"type": "keyword"},
        "targets": {"type": "text"},
        "depth": {"type": "keyword"},
        "features": {"type": "keyword"},
        "steps_count": {"type": "integer"},
        "estimated_duration": {"type": "integer"},
        "prompt_hash": {"type": "keyword"},
        "plan_summary": {"type": "text"}
    }
}

ACTIONS_INDEX_MAPPING = {
    "properties": {
        "run_id": {"type": "keyword"},
        "step_id": {"type": "keyword"},
        "plan_id": {"type": "keyword"},
        "tenant_id": {"type": "keyword"},
        "agent": {"type": "keyword"},
        "tool": {"type": "keyword"},
        "action_type": {"type": "keyword"},
        "status": {"type": "keyword"},
        "started_at": {"type": "date"},
        "ended_at": {"type": "date"},
        "duration_ms": {"type": "integer"},
        "target": {"type": "text"},
        "params": {"type": "object"},
        "result": {"type": "object"},
        "artifacts": {"type": "object"},
        "error_message": {"type": "text"},
        "findings_count": {"type": "integer"}
    }
}

RUNS_INDEX_MAPPING = {
    "properties": {
        "run_id": {"type": "keyword"},
        "plan_id": {"type": "keyword"},
        "tenant_id": {"type": "keyword"},
        "status": {"type": "keyword"},
        "started_at": {"type": "date"},
        "ended_at": {"type": "date"},
        "duration_ms": {"type": "integer"},
        "steps_count": {"type": "integer"},
        "steps_completed": {"type": "integer"},
        "steps_failed": {"type": "integer"},
        "total_findings": {"type": "integer"},
        "high_severity_findings": {"type": "integer"},
        "medium_severity_findings": {"type": "integer"},
        "low_severity_findings": {"type": "integer"},
        "targets_scanned": {"type": "integer"},
        "model_provider": {"type": "keyword"},
        "features_executed": {"type": "keyword"},
        "final_report": {"type": "object"}
    }
}

# Test indices configuration
TEST_INDICES_CONFIG = {
    "cybrty-planner": {"mapping": PLANNER_INDEX_MAPPING},
    "cybrty-actions": {"mapping": ACTIONS_INDEX_MAPPING},
    "cybrty-runs": {"mapping": RUNS_INDEX_MAPPING}
}
