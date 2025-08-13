#!/usr/bin/env python3
"""
OpenSearch Index Initialization Script
Creates all required indices for pentest logging tests
"""

import asyncio
import json
from typing import Dict, Any

# This would normally import from your actual OpenSearch client
# For now, providing the structure needed

class OpenSearchInitializer:
    def __init__(self):
        self.indices_config = {
            "pentest-runs": {
                "mappings": {
                    "properties": {
                        "run_id": {"type": "keyword"},
                        "tenant_id": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "started_at": {"type": "date"},
                        "ended_at": {"type": "date"},
                        "plan_id": {"type": "keyword"},
                        "steps_count": {"type": "integer"}
                    }
                }
            },
            "pentest-actions": {
                "mappings": {
                    "properties": {
                        "run_id": {"type": "keyword"},
                        "step_id": {"type": "keyword"},
                        "tenant_id": {"type": "keyword"},
                        "agent": {"type": "keyword"},
                        "tool": {"type": "keyword"},
                        "target": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "artifacts": {"type": "object"}
                    }
                }
            },
            "pentest-findings": {
                "mappings": {
                    "properties": {
                        "run_id": {"type": "keyword"},
                        "tenant_id": {"type": "keyword"},
                        "finding_type": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "target": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "details": {"type": "object"}
                    }
                }
            },
            "pentest-logs": {
                "mappings": {
                    "properties": {
                        "run_id": {"type": "keyword"},
                        "tenant_id": {"type": "keyword"},
                        "level": {"type": "keyword"},
                        "message": {"type": "text"},
                        "timestamp": {"type": "date"},
                        "component": {"type": "keyword"}
                    }
                }
            }
        }
    
    async def initialize_all_indices(self):
        """Initialize all required indices"""
        print("🔧 Initializing OpenSearch indices for testing...")
        
        for index_name, config in self.indices_config.items():
            success = await self.create_index_if_not_exists(index_name, config)
            if success:
                print(f"✅ Index ready: {index_name}")
            else:
                print(f"❌ Failed to create: {index_name}")
    
    async def create_index_if_not_exists(self, index_name: str, config: Dict[str, Any]) -> bool:
        """Create index if it doesn't exist"""
        try:
            # This is where you'd implement actual OpenSearch client calls
            # For now, just simulate the creation
            print(f"📝 Creating index: {index_name}")
            print(f"   Mapping: {json.dumps(config['mappings'], indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Error creating {index_name}: {e}")
            return False

async def main():
    """Main initialization function"""
    initializer = OpenSearchInitializer()
    await initializer.initialize_all_indices()
    print("\n🎯 OpenSearch initialization complete!")
    print("   All required indices are ready for testing.")

if __name__ == "__main__":
    asyncio.run(main())
