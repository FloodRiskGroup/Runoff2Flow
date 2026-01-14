"""
README for IUH NASH LinearRes test suite.

This directory contains automated tests for the IUH NASH LinearRes project.
Tests are organized by component and can be run using pytest.

## Test Coverage

### test_genetic.py
Tests for the genetic algorithm module:
- Individual chromosome creation
- Population generation
- Evolution and fitness selection
- Support for multiple objective functions (Nash-Sutcliffe, RMSE, MAE)

### test_configuration.py
Tests for configuration file handling:
- INI file parsing
- Parameter extraction
- Parameter validation and bounds checking

### test_data_handling.py
Tests for data processing and I/O:
- Time series handling and continuous period detection
- Missing data encoding (negative values convention)
- Date/time conversion and formatting
- SQLite database operations
- Data validation

### test_workflow_integration.py
Integration tests for complete workflow:
- Project structure verification
- Configuration file accessibility
- Module importability
- Workflow phase structure
- Documentation completeness

## Running Tests

Install pytest (if not already installed):
```bash
pip install pytest
```

Run all tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_genetic.py
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run with coverage report (requires pytest-cov):
```bash
pip install pytest-cov
pytest tests/ --cov=script_run_model --cov=script_project_setup
```

## Test Design

Tests are designed to:
1. **Verify correctness**: Ensure core functions work as intended
2. **Catch regressions**: Detect unintended changes to behavior
3. **Document usage**: Show how to use the software API
4. **Support reproducibility**: Enable automated validation

## Continuous Integration

These tests are intended to be run automatically via GitHub Actions
on every commit. See .github/workflows/ for CI/CD configuration.

## Adding New Tests

When adding new functionality:
1. Add corresponding test cases in the appropriate test file
2. Follow the existing test naming convention: `test_<function_name>`
3. Use fixtures from conftest.py for common test data
4. Include docstrings explaining what each test verifies
"""
