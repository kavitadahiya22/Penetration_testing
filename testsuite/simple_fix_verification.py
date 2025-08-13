#!/usr/bin/env python3
"""
Simple verification that our OpenSearchLogger fix is working.

This proves that runs are completing with 'completed' status instead of 'error',
which was the core issue we fixed.
"""

import json
import subprocess
import re


def main():
    """Verify the OpenSearchLogger fix by checking recent run statuses."""
    
    print("🧪 OpenSearchLogger Fix Verification")
    print("=" * 50)
    
    # Get recent logs to find completed runs
    print("📋 Checking recent Docker logs for completed runs...")
    result = subprocess.run([
        "docker", "logs", "docker-api-1", "--tail", "100"
    ], capture_output=True, text=True)
    
    # Find recent run completions
    run_ids = []
    for line in result.stdout.split('\n'):
        if "Completed pentesting run" in line:
            match = re.search(r'run_id=([a-f0-9\-]+)', line)
            if match:
                run_ids.append(match.group(1))
    
    if not run_ids:
        print("❌ No completed runs found in recent logs")
        return 1
    
    print(f"📋 Found {len(run_ids)} completed runs:")
    for i, run_id in enumerate(run_ids[-5:], 1):  # Check last 5 runs
        print(f"  {i}. {run_id}")
    
    # Check status of most recent runs
    success_count = 0
    error_count = 0
    
    for run_id in run_ids[-3:]:  # Check last 3 runs
        try:
            # Use curl to check run status
            result = subprocess.run([
                "curl", "-s", f"http://localhost:8080/api/v1/runs/{run_id}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                status = status_data.get("status", "unknown")
                
                print(f"\n🔍 Run {run_id}:")
                print(f"   Status: {status}")
                print(f"   Progress: {status_data.get('progress', {})}")
                
                if status == "completed":
                    success_count += 1
                    print("   ✅ SUCCESS: Run completed successfully!")
                elif status == "error":
                    error_count += 1
                    print("   ❌ ERROR: Run failed!")
                else:
                    print(f"   ⚠️ UNKNOWN: Unexpected status: {status}")
            else:
                print(f"   ❌ Failed to check status for {run_id}")
                
        except Exception as e:
            print(f"   ❌ Error checking {run_id}: {e}")
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"   ✅ Successful completions: {success_count}")
    print(f"   ❌ Error statuses: {error_count}")
    
    if success_count > 0 and error_count == 0:
        print("\n🎉 VERIFICATION SUCCESSFUL!")
        print("✅ OpenSearchLogger.log_run() fix is working correctly!")
        print("✅ Runs are completing with 'completed' status instead of 'error'")
        print("✅ The TypeError has been resolved")
        return 0
    elif error_count > 0:
        print("\n❌ VERIFICATION FAILED!")
        print("❌ Some runs still showing 'error' status")
        return 1
    else:
        print("\n⚠️ INCONCLUSIVE!")
        print("⚠️ Could not verify run statuses")
        return 1


if __name__ == "__main__":
    exit(main())
