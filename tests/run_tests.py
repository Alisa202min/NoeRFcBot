#!/usr/bin/env python
"""
RFCBot Testing Utility - Run all system tests and output detailed results
"""

import sys
import os
import unittest
import time
import logging
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_all_tests():
    """Run all tests and log results"""
    # Import the test module
    try:
        from test_system import (
            DatabaseTestCase, 
            WebAppTestCase, 
            ConfigurationTestCase, 
            BotTestCase
        )
        
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add test cases to suite
        test_cases = [
            DatabaseTestCase,
            WebAppTestCase,
            ConfigurationTestCase,
            BotTestCase
        ]
        
        for test_case in test_cases:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
            
        # Capture output
        output = io.StringIO()
        error_output = io.StringIO()
        
        # Run tests with output capture
        logger.info("Starting test run at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        start_time = time.time()
        
        with redirect_stdout(output), redirect_stderr(error_output):
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            
        elapsed_time = time.time() - start_time
        logger.info("Test run completed in %.2f seconds", elapsed_time)
        
        # Log results
        logger.info("Tests run: %d", result.testsRun)
        logger.info("Errors: %d", len(result.errors))
        logger.info("Failures: %d", len(result.failures))
        logger.info("Skipped: %d", len(result.skipped))
        
        # Print detailed test output
        print("\n===== DETAILED TEST OUTPUT =====")
        print(output.getvalue())
        
        if error_output.getvalue():
            print("\n===== ERROR OUTPUT =====")
            print(error_output.getvalue())
            
        # Print errors and failures
        if result.errors:
            print("\n===== ERRORS =====")
            for test, error in result.errors:
                print(f"\nERROR: {test}")
                print(error)
                
        if result.failures:
            print("\n===== FAILURES =====")
            for test, failure in result.failures:
                print(f"\nFAILURE: {test}")
                print(failure)
                
        # Print summary
        print("\n===== TEST SUMMARY =====")
        print(f"Tests run: {result.testsRun}")
        print(f"Errors: {len(result.errors)}")
        print(f"Failures: {len(result.failures)}")
        print(f"Skipped: {len(result.skipped)}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        
        # Return success/failure
        return len(result.errors) == 0 and len(result.failures) == 0
        
    except ImportError as e:
        logger.error("Failed to import test module: %s", str(e))
        print(f"ERROR: Failed to import test module: {str(e)}")
        return False
    except Exception as e:
        logger.error("Unexpected error during test execution: %s", str(e))
        print(f"ERROR: Unexpected error during test execution: {str(e)}")
        return False

def main():
    """Main function to run tests"""
    print("===== RFCBot System Tests =====")
    print(f"Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = run_all_tests()
    
    if success:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()