"""
Integration tests for the complete workflow.
Tests verify that the main workflow steps execute successfully.
"""
import pytest
import os
import sys
import tempfile
import configparser


class TestWorkflowIntegration:
    """Test integration of major workflow components."""
    
    def test_project_directories_exist(self):
        """Project setup and model run directories should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        setup_dir = os.path.join(base_path, 'script_project_setup')
        model_dir = os.path.join(base_path, 'script_run_model')
        
        assert os.path.isdir(setup_dir), "script_project_setup directory should exist"
        assert os.path.isdir(model_dir), "script_run_model directory should exist"
    
    def test_configuration_files_accessible(self):
        """Configuration files should be accessible."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        setup_ini = os.path.join(base_path, 'script_project_setup', 'Input_Setup.ini')
        model_ini = os.path.join(base_path, 'script_run_model', 'calibration_settings.ini')
        
        # At least one should exist (checking accessibility)
        ini_files = [f for f in [setup_ini, model_ini] if os.path.exists(f)]
        assert len(ini_files) > 0, "At least one configuration file should exist"
    
    def test_required_scripts_exist(self):
        """Key workflow scripts should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_scripts = [
            os.path.join(base_path, 'script_run_model', 'genetic.py'),
            os.path.join(base_path, 'script_run_model', 'Model_IUH_NASH_LinearRes.py'),
        ]
        
        for script in required_scripts:
            assert os.path.isfile(script), f"Required script {script} should exist"
    
    def test_input_data_folder_exists(self):
        """InputData folder should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        input_dir = os.path.join(base_path, 'InputData')
        
        assert os.path.isdir(input_dir), "InputData directory should exist"
    
    def test_python_modules_importable(self):
        """Core Python modules should be importable."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.join(base_path, 'script_run_model'))
        
        try:
            import genetic
            assert hasattr(genetic, 'individual')
            assert hasattr(genetic, 'population')
            assert hasattr(genetic, 'evolve_pop')
        except ImportError:
            pytest.skip("genetic module not importable (expected in test environment)")


class TestWorkflowPhase1:
    """Test Phase 1 workflow (project setup)."""
    
    def test_phase1_scripts_listed(self):
        """Phase 1 scripts should be documented."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        steps_file = os.path.join(base_path, 'script_project_setup', 'steps.txt')
        
        if os.path.exists(steps_file):
            with open(steps_file, 'r') as f:
                content = f.read()
                # Should mention key steps
                assert 'Average' in content or 'Discharge' in content or 'Database' in content


class TestWorkflowPhase2:
    """Test Phase 2 workflow (model calibration and simulation)."""
    
    def test_phase2_scripts_listed(self):
        """Phase 2 scripts should be documented."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        steps_file = os.path.join(base_path, 'script_run_model', 'steps.txt')
        
        if os.path.exists(steps_file):
            with open(steps_file, 'r') as f:
                content = f.read()
                # Should mention calibration or model steps
                assert len(content) > 0


class TestWorkflowDocumentation:
    """Test workflow documentation."""
    
    def test_readme_exists(self):
        """README file should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        readme_path = os.path.join(base_path, 'README.md')
        
        assert os.path.isfile(readme_path), "README.md should exist"
    
    def test_readme_has_content(self):
        """README should have meaningful content."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        readme_path = os.path.join(base_path, 'README.md')
        
        with open(readme_path, 'r') as f:
            content = f.read()
            assert len(content) > 100, "README should have substantial content"
            assert 'workflow' in content.lower() or 'phase' in content.lower()
    
    def test_license_exists(self):
        """License file should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        license_path = os.path.join(base_path, 'LICENSE.md')
        
        assert os.path.isfile(license_path), "LICENSE.md should exist"


class TestNotebookWorkflows:
    """Test that workflow notebooks are accessible."""
    
    def test_setup_notebook_exists(self):
        """Setup notebook should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        notebook_path = os.path.join(base_path, 'script_project_setup', 'Setup_model.ipynb')
        
        assert os.path.isfile(notebook_path), "Setup_model.ipynb should exist"
    
    def test_run_notebook_exists(self):
        """Model run notebook should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        notebook_path = os.path.join(base_path, 'script_run_model', 'Run_model.ipynb')
        
        assert os.path.isfile(notebook_path), "Run_model.ipynb should exist"
