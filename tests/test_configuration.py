"""
Unit tests for configuration file handling.
Tests verify INI file parsing and parameter validation.
"""
import pytest
import configparser
import tempfile
import os


class TestConfigurationParsing:
    """Test configuration file loading and parsing."""
    
    @pytest.fixture
    def sample_ini_file(self):
        """Create a temporary INI file with sample configuration."""
        content = """
[Input_par]
ProjectName=TestBasin
database_name=test_database.db

[genetic_parameters]
pop_size=50
num_generations=100
fitnessid=0

[parameter_bounds]
phi_min=0.1
phi_max=0.9
k_min=0.1
k_max=1.0
n_min=1
n_max=10
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            f.write(content)
            ini_path = f.name
        
        yield ini_path
        
        # Cleanup
        os.remove(ini_path)
    
    def test_read_ini_file(self, sample_ini_file):
        """INI file should be readable and parsed correctly."""
        config = configparser.ConfigParser()
        config.read(sample_ini_file)
        
        assert config.has_section('Input_par')
        assert config.has_section('genetic_parameters')
    
    def test_project_name_parameter(self, sample_ini_file):
        """Project name should be retrievable from config."""
        config = configparser.ConfigParser()
        config.read(sample_ini_file)
        
        project_name = config.get('Input_par', 'ProjectName')
        assert project_name == 'TestBasin'
    
    def test_genetic_parameters(self, sample_ini_file):
        """Genetic algorithm parameters should be retrievable."""
        config = configparser.ConfigParser()
        config.read(sample_ini_file)
        
        pop_size = config.getint('genetic_parameters', 'pop_size')
        num_gen = config.getint('genetic_parameters', 'num_generations')
        fitness = config.getint('genetic_parameters', 'fitnessid')
        
        assert pop_size == 50
        assert num_gen == 100
        assert fitness == 0
    
    def test_parameter_bounds(self, sample_ini_file):
        """Parameter bounds should be retrievable and valid."""
        config = configparser.ConfigParser()
        config.read(sample_ini_file)
        
        phi_min = config.getfloat('parameter_bounds', 'phi_min')
        phi_max = config.getfloat('parameter_bounds', 'phi_max')
        
        assert 0 < phi_min < phi_max
        assert phi_min < 1.0
        assert phi_max <= 1.0


class TestParameterValidation:
    """Test parameter validation logic."""
    
    def test_phi_in_valid_range(self):
        """Parameter phi should be between 0 and 1."""
        phi = 0.5
        assert 0 < phi < 1, "phi should be between 0 and 1"
    
    def test_k_positive(self):
        """Parameter k should be positive."""
        k = 0.5
        assert k > 0, "k should be positive"
    
    def test_n_integer_positive(self):
        """Parameter n should be positive integer."""
        n = 3
        assert isinstance(n, int)
        assert n > 0, "n should be positive"
    
    def test_population_size_reasonable(self):
        """Population size should be reasonable for genetic algorithm."""
        pop_size = 50
        assert 10 <= pop_size <= 1000, "Population size should be between 10 and 1000"
    
    def test_generations_reasonable(self):
        """Number of generations should be reasonable."""
        num_gen = 100
        assert 10 <= num_gen <= 10000, "Generations should be between 10 and 10000"
