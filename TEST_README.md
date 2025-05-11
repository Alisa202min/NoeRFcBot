# RFCBot Testing Documentation

## Overview
This repository contains comprehensive test suites for the RFCBot application, covering both the Telegram bot and web admin panel functionality. The tests are organized into several modules to ensure proper coverage of all application components.

## Test Structure

### Basic Tests
- **test_simple.py**: Simple database connectivity and basic operations tests
  - `test_database_connection`: Validates database connection
  - `test_simple_category_creation`: Tests category creation, retrieval, and deletion

### Database Tests
- **test_db.py**: Comprehensive tests for all database operations
  - Tests for categories (add, get, update, delete)
  - Tests for products and services
  - Tests for media handling
  - Tests for educational content
  - Tests for inquiries
  - Tests for static content

### Bot Tests
- **test_bot.py**: Tests for Telegram bot command handlers
  - Command handling tests
  - Message handlers
  - Callback query handling
  - Bot initialization and setup

### Flow Tests
- **test_flows.py**: Tests for conversation flows and user interactions
  - Product browsing flow
  - Category navigation
  - Product search and filtering
  - Price inquiry flow
  - Educational content browsing

### Admin Tests
- **test_admin.py**: Tests for admin panel functionality
  - Admin command access control
  - Category management
  - Product management
  - Media management
  - Educational content management
  - Static content management
  - Inquiry management
  - Data export/import

## Test Fixtures

The tests use pytest fixtures to provide common test objects and data:

- **test_db**: Provides a database instance
- **test_message**: Provides a mock message for testing
- **test_admin_message**: Provides a mock admin message
- **test_callback_query**: Provides a mock callback query
- **test_user**: Provides a mock user for testing

## Running Tests

### Individual Test Files

Run specific test files using:

```bash
# Run database tests
pytest tests/test_db.py -v

# Run bot command tests
pytest tests/test_bot.py -v

# Run conversation flow tests
pytest tests/test_flows.py -v

# Run admin panel tests
pytest tests/test_admin.py -v

# Run simple tests (these are faster and more reliable)
pytest tests/test_simple.py -v
```

### Automated Test Runner

An automated test runner is provided to execute the tests with proper handling of timeouts and reporting:

```bash
# Run automated tests
python run_tests.py
```

The test runner will:
1. Check database connectivity
2. Run the simpler tests
3. Generate a detailed report of test results
4. Log the results to test_results.log and the console

## Test Tips

1. **Database-Dependent Tests**: Some tests require a working database connection. Ensure the DATABASE_URL environment variable is set.

2. **Bot Token**: For tests that involve actual bot API calls, ensure the BOT_TOKEN environment variable is set.

3. **Mocking**: Most tests use mocking to simulate Telegram API calls and user interactions.

4. **Timeouts**: Some tests may timeout in complex scenarios. Use the `-k` flag to run specific test functions if needed:
   ```bash
   # Run a specific test function
   pytest tests/test_flows.py::TestConversationFlows::test_product_browsing -v
   ```

5. **Debugging**: For detailed debugging information, set the log level to DEBUG:
   ```bash
   # Set debug level for more verbose output
   PYTEST_LOG_LEVEL=DEBUG pytest tests/test_bot.py -v
   ```

## Known Issues

1. **Test Dependencies**: Some tests may depend on the state created by other tests. To ensure isolation, use the `-xvs` flags to stop on the first failure and show output:
   ```bash
   pytest tests/test_flows.py -xvs
   ```

2. **Resource Cleanup**: Tests should clean up created resources, but in case of test failures, some test data might remain in the database.

3. **Timeouts**: Complex tests might timeout. Consider running them individually with increased timeout values:
   ```bash
   PYTEST_TIMEOUT=60 pytest tests/test_flows.py::TestConversationFlows::test_product_search -v
   ```