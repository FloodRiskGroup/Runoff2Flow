# Input Data Documentation

## Overview

The `InputData/` folder contains example data required to run the complete IUH NASH LinearRes workflow. These datasets enable users to execute the model without requiring external data downloads.

## Data Files

### Climate Data (NetCDF format)

**RF_1951_2022.nc**
- **Description**: Monthly surface runoff data (1951-2022)
- **Format**: NetCDF4
- **Resolution**: Aggregated to watershed
- **Units**: mm/month (monthly accumulated runoff)
- **Period**: 72 years (monthly data = 864 timesteps)

**GR_1951_2022.nc**
- **Description**: Monthly groundwater recharge data (1951-2022)
- **Format**: NetCDF4
- **Resolution**: Aggregated to watershed
- **Units**: mm/month (monthly accumulated recharge)
- **Period**: 72 years (monthly data = 864 timesteps)

### Discharge Data (CSV format)

**Historical_data_Tolignano.csv**
- **Description**: Observed monthly river discharge at Tolignano outlet
- **Format**: CSV (comma-separated values)
- **Columns**: Date, Discharge (m³/s), Quality flag
- **Units**: m³/s (cubic meters per second)
- **Period**: Historical monthly observations
- **Usage**: Calibration and validation target for the model

### Geospatial Data (GeoPackage format)

**outlet_catchment.gpkg**
- **Description**: Watershed boundary/catchment polygon
- **Format**: GeoPackage (OGC-compliant geodatabase)
- **Geometry**: Polygon
- **Coordinate System**: WGS84 (EPSG:4326) or local projection
- **Usage**: Basin delineation and spatial reference

**outlet_point.gpkg**
- **Description**: Basin outlet point location
- **Format**: GeoPackage (OGC-compliant geodatabase)
- **Geometry**: Point
- **Coordinate System**: WGS84 (EPSG:4326) or local projection
- **Usage**: Model outlet definition for discharge extraction

---

## Using Example Data

The example data is automatically loaded when you run the workflow scripts:

```bash
# Phase 1: Processes the NetCDF and CSV files
python script_project_setup/Average_watershed_values.py
python script_project_setup/Load_Discharge_RSE_file.py

# Phase 2: Uses processed data for calibration
python script_run_model/Model_calibration.py
```

---

## Replacing with Your Own Data

To use the model with your own data:

1. **Prepare climate data** as NetCDF files with monthly timesteps (RF and GR)
2. **Prepare discharge data** as CSV with Date and Discharge columns
3. **Prepare geospatial data** as GeoPackage files with catchment polygon and outlet point
4. **Update configuration** in `Input_Setup.ini` and `calibration_settings.ini` with your file paths
5. **Run the workflow** normally

---

## Data Formats & Specifications

### NetCDF Climate Data
- Variables: values (1D time series)
- Dimensions: time
- Attributes: long_name, units, calendar
- Example: `RF_1951_2022.nc` → 864 timesteps of surface runoff

### CSV Discharge Data
```
Date,Discharge
1951-01-01,25.5
1951-02-01,28.3
...
```

### GeoPackage Geospatial Data
- Layer: features (polygon or point geometry)
- Projection: WGS84 or local UTM zone
- Attributes: feature_name, area_km2 (optional)

---

## References & Attribution

For information about data sources and processing methods, see:
- [paper/paper.md](../paper/paper.md) - Scientific paper with methodology
- [SETUP.md](../SETUP.md) - Installation and setup guide
- Configuration files: `Input_Setup.ini`, `calibration_settings.ini`

---

## Contact & Questions

If you have questions about the example data or need assistance preparing your own data:
- See [README.md](../README.md) for project overview
- Check example workflow in [script_project_setup/Setup_model.ipynb](../script_project_setup/Setup_model.ipynb)
- Review configuration documentation in INI files
