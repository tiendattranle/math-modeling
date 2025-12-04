#!/usr/bin/env python3
"""
Script to run all test cases for Petri Net Analyzer
Automatically finds all .xml test files and runs the analyzer on each one.
"""

import os
import sys
import subprocess
import glob
from datetime import datetime

def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)

def print_header(text):
    """Print a formatted header"""
    print_separator()
    print(f" {text}")
    print_separator()

def run_test(test_file, weights=None):
    """
    Run a single test case
    
    Args:
        test_file: Path to the test XML file
        weights: Optional weight string (e.g., "1,2,3")
    """
    print_header(f"Running: {test_file}")
    
    # Build command
    cmd = [sys.executable, "petri_net_analyzer.py", test_file]
    if weights:
        cmd.append(weights)
    
    # Run the analyzer
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        # Print output
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            print(f"	Test failed with return code: {result.returncode}")
            return False
        else:
            print(f"	Test completed successfully")
            return True
            
    except subprocess.TimeoutExpired:
        print(f"	Test timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"	Error running test: {e}")
        return False

def main():
    """Main function to run all tests"""
    print_header(f"PETRI NET ANALYZER - TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Find all XML test files
    test_files = sorted(glob.glob("*.xml"))
    
    if not test_files:
        print("	No test files found in current directory")
        return 1
    
    print(f"Found {len(test_files)} test file(s):")
    for i, test_file in enumerate(test_files, 1):
        print(f"  {i}. {test_file}")
    print()
    
    # Track results
    results = {}
    
    # Run each test
    for test_file in test_files:
        success = run_test(test_file)
        results[test_file] = success
        print()  # Empty line between tests
    
    # Print summary
    print_separator('=', 80)
    print(" TEST SUMMARY")
    print_separator('=', 80)
    
    passed = sum(1 for success in results.values() if success)
    failed = len(results) - passed
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"	Passed: {passed}")
    print(f"	Failed: {failed}")
    print()
    
    # List results
    for test_file, success in results.items():
        status = "	PASS" if success else "	FAIL"
        print(f"  {status} - {test_file}")
    
    print()
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator('=', 80)
    
    # Return exit code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
