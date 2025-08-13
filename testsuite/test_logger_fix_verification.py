#!/usr/bin/env python3
"""
Verification test for OpenSearchLogger fix.

This test verifies that the OpenSearchLogger.log_run() method signature fix
is working correctly by starting a pentest run and then polling for completion.
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any


async def verify_logger_fix():
    """Verify that the OpenSearchLogger fix is working by testing a pentest run."""
    
    # Test configuration
    api_base = "http://localhost:8080/api/v1"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # First, verify API is healthy
        print("🔍 Checking API health...")
        health_response = await client.get(f"{api_base}/health")
        print(f"✅ API Health: {health_response.json()}")
        
        # Start a pentest run (this should not hang on response if our fix works)
        print("\n🚀 Starting pentest run...")
        run_input = {
            "tenant_id": "test-logger-fix",
            "inputs": {
                "targets": ["10.0.0.75"],
                "depth": "quick", 
                "features": ["creds"],
                "simulate": True
            }
        }
        
        # Try to start run with short timeout - if our fix works, the backend will process
        # even if response times out
        try:
            start_time = time.time()
            response = await client.post(f"{api_base}/agents/pentest/run", json=run_input)
            end_time = time.time()
            run_id = response.json()["run_id"]
            print(f"✅ Run started successfully: {run_id} (took {end_time-start_time:.2f}s)")
            
        except httpx.ReadTimeout:
            print("⚠️ POST request timed out, but backend may still be processing...")
            run_id = None
            
        # If we didn't get a run_id from the response, check recent runs
        if run_id is None:
            print("\n🔍 Checking for recent runs...")
            # Give backend a moment to process
            await asyncio.sleep(3)
            
            # Look at recent logs to find our run
            import subprocess
            result = subprocess.run([
                "docker", "logs", "docker-api-1", "--tail", "50"
            ], capture_output=True, text=True)
            
            lines = result.stdout.split('\n')
            print("📋 Recent logs:")
            for line in lines[-10:]:
                if line.strip():
                    print(f"  {line}")
            
            # Look for our tenant_id in the logs
            for line in lines:
                if "test-logger-fix" in line and "run_id=" in line:
                    # Extract run_id from log line like: "run_id=abc-123-def"
                    import re
                    match = re.search(r'run_id=([a-f0-9\-]+)', line)
                    if match:
                        run_id = match.group(1)
                        print(f"📋 Found run_id from logs: {run_id}")
                        break
        
        if run_id is None:
            print("❌ Could not determine run_id")
            return False
            
        # Check run status to verify our fix worked
        print(f"\n🔍 Checking run status for: {run_id}")
        for attempt in range(5):
            try:
                status_response = await client.get(f"{api_base}/runs/{run_id}")
                status_data = status_response.json()
                print(f"📊 Run Status (attempt {attempt + 1}): {json.dumps(status_data, indent=2)}")
                
                if status_data.get("status") == "completed":
                    print("\n🎉 SUCCESS! Run completed successfully!")
                    print("✅ OpenSearchLogger.log_run() fix is working!")
                    return True
                elif status_data.get("status") == "error":
                    print("\n❌ FAILURE! Run failed with error status")
                    print("❌ OpenSearchLogger fix may not be working")
                    return False
                else:
                    print(f"⏳ Run still in progress: {status_data.get('status', 'unknown')}")
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                await asyncio.sleep(1)
        
        print("\n⏰ Run did not complete within timeout period")
        return False


async def main():
    """Main verification function."""
    print("🧪 OpenSearchLogger Fix Verification Test")
    print("=" * 50)
    
    try:
        success = await verify_logger_fix()
        if success:
            print("\n🎉 VERIFICATION SUCCESSFUL!")
            print("✅ The OpenSearchLogger.log_run() method signature fix is working correctly")
            print("✅ Runs complete with 'completed' status instead of 'error'")
            return 0
        else:
            print("\n❌ VERIFICATION FAILED!")
            print("❌ The fix may not be working correctly")
            return 1
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
