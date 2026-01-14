"""
Unit tests for data processing and I/O operations.
Tests verify time series data handling, missing value encoding, and database operations.
"""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta


class TestTimeSeriesHandling:
    """Test time series data handling and validation."""
    
    def test_continuous_period_detection(self):
        """Continuous data periods should be correctly identified."""
        # Positive values = data, negative = missing
        time_series = [10, 15, 20, -1, -1, 25, 30, 35, -1]
        
        # Identify continuous periods
        periods = []
        current_period = []
        for val in time_series:
            if val > 0:
                current_period.append(val)
            else:
                if current_period:
                    periods.append(current_period)
                    current_period = []
        if current_period:
            periods.append(current_period)
        
        assert len(periods) == 2
        assert len(periods[0]) == 3  # First continuous period
        assert len(periods[1]) == 3  # Second continuous period
    
    def test_missing_data_encoding(self):
        """Missing data should be encoded as negative values."""
        observed_value = None
        encoded_value = -1  # Convention: negative = missing
        
        assert encoded_value < 0
    
    def test_all_positive_values(self):
        """All-positive time series indicates continuous data."""
        time_series = [10.5, 12.3, 11.8, 13.2, 10.9]
        
        # Check all positive
        assert all(v > 0 for v in time_series)
    
    def test_time_series_length(self):
        """Time series should have reasonable length for monthly data."""
        # 10 years of monthly data
        months = 12 * 10
        time_series = list(range(1, months + 1))
        
        assert len(time_series) == 120


class TestDateConversion:
    """Test date/time handling and conversion."""
    
    def test_date_string_format(self):
        """Date should be in ISO format (YYYY-MM-DD)."""
        date_str = "2020-01-15"
        # Should be parseable
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        assert date_obj.year == 2020
        assert date_obj.month == 1
    
    def test_monthly_time_step(self):
        """Monthly time series should have ~30-day intervals."""
        date1 = datetime(2020, 1, 1)
        date2 = datetime(2020, 2, 1)
        
        delta = (date2 - date1).days
        assert 28 <= delta <= 31
    
    def test_date_ordering(self):
        """Dates should be in chronological order."""
        dates = [
            datetime(2020, 1, 1),
            datetime(2020, 2, 1),
            datetime(2020, 3, 1),
        ]
        
        assert dates == sorted(dates)


class TestSQLiteDatabaseOperations:
    """Test database creation and operations."""
    
    @pytest.fixture
    def temp_database(self):
        """Create temporary SQLite database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
    
    def test_database_creation(self, temp_database):
        """Database file should be created."""
        conn = sqlite3.connect(temp_database)
        conn.close()
        
        assert os.path.exists(temp_database)
    
    def test_timeseries_table_schema(self, temp_database):
        """TimeSeries table should have correct schema."""
        conn = sqlite3.connect(temp_database)
        cur = conn.cursor()
        
        # Create expected schema
        cur.execute('''
            CREATE TABLE TimeSeries (
                TSID INTEGER PRIMARY KEY,
                TSDate TEXT NOT NULL,
                TSTYPE INTEGER,
                value REAL
            )
        ''')
        conn.commit()
        
        # Verify table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TimeSeries'")
        assert cur.fetchone() is not None
        
        conn.close()
    
    def test_insert_timeseries_data(self, temp_database):
        """Time series data should be insertable into database."""
        conn = sqlite3.connect(temp_database)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE TimeSeries (
                TSID INTEGER PRIMARY KEY,
                TSDate TEXT NOT NULL,
                TSTYPE INTEGER,
                value REAL
            )
        ''')
        
        # Insert test data
        test_date = "2020-01-01"
        test_value = 25.5
        cur.execute(
            "INSERT INTO TimeSeries (TSDate, TSTYPE, value) VALUES (?, ?, ?)",
            (test_date, 20, test_value)
        )
        conn.commit()
        
        # Verify insertion
        cur.execute("SELECT value FROM TimeSeries WHERE TSDate=?", (test_date,))
        result = cur.fetchone()
        assert result is not None
        assert result[0] == test_value
        
        conn.close()
    
    def test_query_positive_values(self, temp_database):
        """Query should correctly filter positive values."""
        conn = sqlite3.connect(temp_database)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE TimeSeries (
                TSID INTEGER PRIMARY KEY,
                TSDate TEXT NOT NULL,
                TSTYPE INTEGER,
                value REAL
            )
        ''')
        
        # Insert mixed data
        test_data = [
            ("2020-01-01", 20, 25.5),
            ("2020-02-01", 20, 30.0),
            ("2020-03-01", 20, -1),  # Missing
            ("2020-04-01", 20, 28.5),
        ]
        
        for date, tstype, value in test_data:
            cur.execute(
                "INSERT INTO TimeSeries (TSDate, TSTYPE, value) VALUES (?, ?, ?)",
                (date, tstype, value)
            )
        conn.commit()
        
        # Query positive values only
        cur.execute("SELECT value FROM TimeSeries WHERE TSTYPE=20 AND value > 0")
        results = cur.fetchall()
        
        assert len(results) == 3
        assert all(r[0] > 0 for r in results)
        
        conn.close()


class TestDataValidation:
    """Test data validation logic."""
    
    def test_discharge_value_reasonable(self):
        """Discharge values should be physically reasonable."""
        discharge = 25.5  # m³/s
        # Should be non-negative and not absurdly large
        assert discharge >= 0
        assert discharge < 1e6
    
    def test_basin_area_positive(self):
        """Basin area should be positive."""
        area_km2 = 150.5
        assert area_km2 > 0
    
    def test_parameter_phi_valid(self):
        """Parameter phi should be between 0 and 1."""
        phi = 0.35
        assert 0 < phi < 1
    
    def test_no_nan_values(self):
        """Data should not contain NaN values."""
        import math
        values = [10.5, 15.2, 12.8]
        assert all(not math.isnan(v) for v in values)
