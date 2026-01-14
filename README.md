# IUH NASH LinearRes

[![Tests](https://github.com/FloodRiskGroup/Runoff2Flow/actions/workflows/tests.yml/badge.svg)](https://github.com/FloodRiskGroup/Runoff2Flow/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**IUH NASH LinearRes** is a hydrological modeling framework for reconstructing monthly river discharge using an Instantaneous Unit Hydrograph (IUH) Nash model combined with a linear reservoir representation of baseflow. The software is designed for data-scarce basins and long-term historical analyses where continuous discharge observations are unavailable or incomplete.

The framework integrates surface runoff and groundwater recharge inputs with observed discharge data, calibrates model parameters using a genetic algorithm, and reconstructs discharge over the full historical period. Flow-duration curves are provided for frequency analysis.

---

## Statement of need

Reliable river discharge time series are essential for hydrological analysis and water resources management, yet many river basins lack continuous long-term discharge observations. Existing hydrological modeling systems often focus on daily or sub-daily simulations, require complex parameterization, or do not provide reproducible workflows for discharge reconstruction at monthly resolution.

IUH NASH LinearRes addresses this gap by providing a lightweight, reproducible, and configuration-driven framework for monthly discharge reconstruction based on the IUH Nash concept and linear reservoir modeling. The software emphasizes transparency, database-centered data handling, and reproducible calibration using genetic algorithms, making it suitable for comparative basin studies and historical reconstructions.

---

## Project structure

```text
iuh_nash_linearres/
│
├── InputData/                  # Climate, discharge, and geospatial inputs
│   ├── RF_1951_2022.nc          # Surface runoff (NetCDF)
│   ├── GR_1951_2022.nc          # Groundwater recharge (NetCDF)
│   ├── Historical_data_*.csv    # Observed discharge
│   ├── outlet_catchment.gpkg
│   └── outlet_point.gpkg
│
├── script_project_setup/        # Data preparation and database creation
│
├── script_run_model/            # Calibration, simulation, and analysis
│
├── environment.yml              # Conda environment specification
└── README.md
```
## Workflow overview

The modeling workflow is divided into two phases.

### Phase 1: Project setup
1. Watershed averaging of runoff and recharge
2. Loading observed discharge
3. SQLite database creation
4. Upload of time series
5. Optional visualization

Scripts are located in `script_project_setup/` and are executed sequentially.

### Phase 2: Model calibration and simulation
1. Inspection of observed discharge
2. Train/test period selection
3. Genetic algorithm calibration
4. Full-period discharge reconstruction
5. Flow-duration curve computation

Scripts are located in `script_run_model/`.

---

## Installation

A Conda environment is recommended. 

**Quick start:**
```bash
conda env create -f environment.yml
conda activate IUH
```

---

## Testing

Automated tests verify core functionality:

```bash
pytest tests/ -v
```

Test suite includes:
- Genetic algorithm validation
- Configuration file handling
- Data processing and I/O
- Workflow integration

See [tests/README.md](tests/README.md) for details.

---

## Quick Start Example

1. **Setup environment** (see [SETUP.md](SETUP.md)):
```bash
conda env create -f environment.yml
conda activate IUH
```

2. **Run Phase 1** (project setup with example data):
```bash
cd script_project_setup
python Average_watershed_values.py    # Process climate data
python Load_Discharge_RSE_file.py     # Load observed discharge
python CreateDatabaseSqlite.py        # Create database
python Upload_TimeSeries.py           # Upload to database
```

3. **Run Phase 2** (model calibration):
```bash
cd ../script_run_model
python Graph_observed_data.py         # Visualize input data
python Split_train_test.py            # Split calibration/validation
python Model_calibration.py           # Calibrate with genetic algorithm
python Model_IUH_NASH_LinearRes_calc_period.py  # Full period simulation
python Flow-duration_curve.py         # Generate flow-duration curves
```

For interactive workflow, see Jupyter notebooks in each folder.

---
