"""
Shared pytest fixtures for IUH NASH LinearRes tests.
"""
import pytest
import tempfile
import sqlite3
import os
from datetime import datetime, timedelta


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_timeseries():
    """Generate sample time series data for testing."""
    dates = []
    values = []
    base_date = datetime(2000, 1, 1)
    
    # Generate 120 months of continuous data
    for i in range(120):
        dates.append(base_date + timedelta(days=30*i))
        values.append(50 + i*0.5)  # Linear trend
    
    return list(zip(dates, values))


@pytest.fixture
def sample_parameters():
    """Sample model parameters for testing."""
    return {
        'basin_area_km2': 100.0,
        'phi': 0.3,
        'k': 0.5,
        'n': 3,
        'Ps': 200.0
    }


@pytest.fixture
def sample_chromosome():
    """Sample genetic algorithm chromosome."""
    return [30, 50, 5, 3, 100]  # [phi, k, n, num_reservoirs, Ps]
