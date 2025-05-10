"""
Web Application Test Runner for RFCBot
"""

import unittest
import logging
from test_system import WebAppTestCase

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

def run_web_tests():
    """Run web application tests only"""
    logger.info("Starting web tests")
    
    # Create test suite with WebAppTestCase only
    suite = unittest.TestLoader().loadTestsFromTestCase(WebAppTestCase)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Log results
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    # Print detailed errors and failures
    if result.errors:
        logger.error("--- Errors ---")
        for test, error in result.errors:
            logger.error(f"Error in {test}: {error}")
    
    if result.failures:
        logger.error("--- Failures ---")
        for test, failure in result.failures:
            logger.error(f"Failure in {test}: {failure}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("===== RFCBot Web Tests =====")
    success = run_web_tests()
    print(f"Tests {'passed' if success else 'failed'}")