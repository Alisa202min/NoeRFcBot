name: Run Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:latest
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: rfcbot_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
        env:
          TEST_BOT_TOKEN: ${{ secrets.TEST_BOT_TOKEN }}
          DB_NAME: rfcbot_test
          DB_USER: test_user
          DB_PASSWORD: test_password
          DB_HOST: localhost
          DB_PORT: 5432