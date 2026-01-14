"""
Unit tests for genetic algorithm module (script_run_model/genetic.py).
Tests verify basic genetic algorithm operations: population creation,
fitness evaluation, and evolution.
"""
import pytest
import sys
import os

# Add parent directory to path to import genetic module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'script_run_model'))

from genetic import individual, population, evolve_pop


class TestIndividualCreation:
    """Test chromosome/individual creation."""
    
    def test_individual_length(self):
        """Individual should have correct chromosome length."""
        ind = individual(length=5, min=0, max=100)
        assert len(ind) == 5
    
    def test_individual_values_in_range(self):
        """Individual values should be within min/max bounds."""
        ind = individual(length=4, min=10, max=50)
        assert all(10 <= x <= 50 for x in ind)
    
    def test_individual_non_empty(self):
        """Individual should not be empty."""
        ind = individual(length=1, min=0, max=100)
        assert len(ind) > 0
    
    def test_individual_zero_length(self):
        """Individual with zero length should be empty."""
        ind = individual(length=0, min=0, max=100)
        assert len(ind) == 0


class TestPopulationCreation:
    """Test population creation."""
    
    def test_population_size(self):
        """Population should have correct number of individuals."""
        pop = population(count=10, length=4, min=0, max=100)
        assert len(pop) == 10
    
    def test_population_individual_size(self):
        """Each individual in population should have correct length."""
        pop = population(count=5, length=6, min=0, max=100)
        assert all(len(ind) == 6 for ind in pop)
    
    def test_population_values_in_range(self):
        """All population values should be within bounds."""
        pop = population(count=10, length=5, min=20, max=80)
        for ind in pop:
            assert all(20 <= x <= 80 for x in ind)
    
    def test_empty_population(self):
        """Empty population should have no individuals."""
        pop = population(count=0, length=4, min=0, max=100)
        assert len(pop) == 0


class MockIndividualWithFitness:
    """Mock individual class with fitness attributes for testing evolution."""
    
    def __init__(self, chromosomes, eff=0.5, rmse=10.0, mae=8.0):
        self.chromosomes = chromosomes.copy()
        self.Eff = eff  # Nash-Sutcliffe
        self.RMSE = rmse
        self.MAE = mae


class TestEvolutionAlgorithm:
    """Test genetic algorithm evolution step."""
    
    def test_evolve_pop_nash_sutcliffe_sorting(self):
        """Evolution with Nash-Sutcliffe should maximize fitness."""
        pop = [
            MockIndividualWithFitness([1, 2, 3], eff=0.3),
            MockIndividualWithFitness([4, 5, 6], eff=0.8),
            MockIndividualWithFitness([7, 8, 9], eff=0.5),
            MockIndividualWithFitness([10, 11, 12], eff=0.6),
            MockIndividualWithFitness([13, 14, 15], eff=0.4),
        ]
        
        parents, eff_list, graded = evolve_pop(pop, fitnessid=0, retain=0.4)
        
        # Best individual (Eff=0.8) should be first in fitness list
        assert eff_list[0] >= eff_list[-1]
        # List should be sorted descending
        assert eff_list == sorted(eff_list, reverse=True)
    
    def test_evolve_pop_rmse_sorting(self):
        """Evolution with RMSE should minimize fitness (lower is better)."""
        pop = [
            MockIndividualWithFitness([1, 2, 3], rmse=15.0),
            MockIndividualWithFitness([4, 5, 6], rmse=5.0),
            MockIndividualWithFitness([7, 8, 9], rmse=10.0),
            MockIndividualWithFitness([10, 11, 12], rmse=8.0),
            MockIndividualWithFitness([13, 14, 15], rmse=12.0),
        ]
        
        parents, rmse_list, graded = evolve_pop(pop, fitnessid=1, retain=0.4)
        
        # Best individual (RMSE=5.0) should be first
        assert rmse_list[0] <= rmse_list[-1]
        # List should be sorted ascending (minimization)
        assert rmse_list == sorted(rmse_list, reverse=False)
    
    def test_evolve_pop_mae_sorting(self):
        """Evolution with MAE should minimize fitness."""
        pop = [
            MockIndividualWithFitness([1, 2, 3], mae=12.0),
            MockIndividualWithFitness([4, 5, 6], mae=4.0),
            MockIndividualWithFitness([7, 8, 9], mae=8.0),
            MockIndividualWithFitness([10, 11, 12], mae=6.0),
            MockIndividualWithFitness([13, 14, 15], mae=10.0),
        ]
        
        parents, mae_list, graded = evolve_pop(pop, fitnessid=2, retain=0.4)
        
        # Best individual (MAE=4.0) should be first
        assert mae_list[0] <= mae_list[-1]
        # List should be sorted ascending
        assert mae_list == sorted(mae_list, reverse=False)
    
    def test_evolve_pop_retention(self):
        """Evolution should retain specified fraction of best individuals."""
        pop = [MockIndividualWithFitness([i], eff=0.1*i) for i in range(1, 11)]
        
        parents, eff_list, graded = evolve_pop(pop, fitnessid=0, retain=0.2)
        
        # Should have population-sized result
        assert len(parents) == len(pop)
    
    def test_evolve_pop_returns_arrays(self):
        """Evolution should return parents, fitness list, and graded chromosomes."""
        pop = [MockIndividualWithFitness([i*10], eff=0.1*i) for i in range(1, 11)]
        
        parents, eff_list, graded = evolve_pop(pop, fitnessid=0, retain=0.2)
        
        assert isinstance(parents, list)
        assert isinstance(eff_list, list)
        assert isinstance(graded, list)
        assert len(eff_list) == len(pop)
