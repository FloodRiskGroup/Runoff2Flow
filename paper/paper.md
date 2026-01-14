---
title: "IUH NASH LinearRes: A reproducible framework for monthly river discharge reconstruction using IUH Nash and linear reservoir modeling"
tags:
  - hydrology
  - river discharge
  - IUH Nash
  - linear reservoir
  - genetic algorithm
  - hydrological modeling
authors:
  - name: Leonardo Mancusi
    affiliation: 1
  - name: Giovanni Braca
    affiliation: 2
  - name: Alessandro Amaranto
    affiliation: 1
affiliations:
  - name: Sustainable Development and Energy Sources Department, RSE Ricerca sul Sistema Energetico, Milano, Italy
    index: 1
  - name: ISPRA – Istituto Superiore per la Protezione e la Ricerca Ambientale, Roma, Italy
    index: 2
date: 2026
bibliography: paper.bib
---

## Summary

Reliable river discharge time series are essential for hydrological analysis, water resources management, and climate impact assessment. However, many river basins lack continuous long-term discharge observations, particularly when analyses are conducted at monthly temporal resolution or over historical periods. **IUH NASH LinearRes** is an open-source, configuration-driven framework for reconstructing monthly river discharge using an Instantaneous Unit Hydrograph (IUH) Nash model combined with a linear reservoir representation of baseflow. The software integrates surface runoff and groundwater recharge inputs with observed discharge data, calibrates model parameters using a genetic algorithm, and reconstructs discharge over extended historical periods. A database-centered architecture based on SQLite ensures reproducible data handling, while script-based workflows support calibration, validation, and flow-duration curve analysis. The framework is intended for hydrologists and environmental scientists working in data-scarce or partially observed basins.

---

## Statement of need

Continuous and reliable river discharge records are a fundamental requirement for hydrological studies [@NashSutcliffe1970; @Moriasi2007], yet observational gaps remain widespread due to limited monitoring infrastructure, historical data discontinuities, and changes in measurement practices. Existing hydrological modeling frameworks often emphasize daily or sub-daily simulations [@Arnold2012; @Bergström1976], require extensive parameterization, or rely on complex model structures [@Todini1996] that are not always suitable for monthly-scale discharge reconstruction or historical analyses.

IUH NASH LinearRes addresses this gap by providing a lightweight and reproducible framework specifically designed for monthly river discharge reconstruction using aggregated climate inputs. The software implements an IUH Nash cascade [@Nash1957; @Dooge1959] coupled with a linear reservoir model to represent basin response and baseflow dynamics [@Eckhardt2005], and employs a genetic algorithm for parameter calibration across multiple objective functions [@Goldberg1989; @Duan1992]. Unlike monolithic hydrological modeling systems, IUH NASH LinearRes emphasizes transparency, modularity, and configuration-driven execution [@Beven1989]. Its database-centered architecture enables traceable data management, explicit handling of missing observations, and reproducible calibration–validation workflows [@Klemes1986].

The software is intended for applications where discharge observations are sparse or incomplete, including comparative basin studies, long-term historical reconstructions, and sensitivity analyses. By combining established hydrological concepts with modern reproducibility practices, IUH NASH LinearRes fills a methodological niche not fully addressed by existing tools.

---

## Software description

### Architecture and workflow

The framework is organized into a two-phase workflow. The first phase focuses on project setup, including watershed averaging of climate inputs, loading of observed discharge data, and creation of a SQLite database to store all time series. The second phase performs model calibration, validation, and simulation, including genetic algorithm optimization, full-period discharge reconstruction, and flow-duration curve analysis.

All workflows are executed through standalone Python scripts, with model parameters and execution options controlled via INI configuration files. This design minimizes hidden dependencies and facilitates reproducible experimentation without modifying source code.

### Hydrological model

The core hydrological model is based on the Instantaneous Unit Hydrograph (IUH) Nash formulation [@Nash1957], representing basin response as a cascade of linear reservoirs. This approach has proven effective for monthly-scale discharge simulations and provides a parsimonious parameterization suitable for data-limited basins. A separate linear reservoir is used to model baseflow contributions driven by groundwater recharge, consistent with baseflow separation methodologies [@Eckhardt2005]. The model operates at monthly temporal resolution and is implemented as a lumped basin-scale representation.

Missing or invalid observations are explicitly encoded using negative values, allowing continuous data periods to be identified programmatically for calibration and validation [@Klemes1986; @Wagener2007].

### Calibration and analysis

Model parameters are calibrated using a custom genetic algorithm implementation [@Goldberg1989; @Yapo1996] that supports multiple objective functions: Nash–Sutcliffe efficiency [@NashSutcliffe1970], root mean square error, and mean absolute error [@Gupta2009; @Moriasi2007]. Calibration and validation periods are selected automatically based on continuous data availability [@Klemes1986]. After calibration, the model reconstructs discharge over the full historical period and computes flow-duration curves for frequency analysis [@Harman2009]. The multi-objective approach allows users to select calibration criteria based on specific applications and data characteristics [@Duan1992].

---

## Example use case

The repository includes example climate, discharge, and geospatial datasets that allow users to execute the full workflow without external data downloads. A typical use case involves configuring basin parameters and calibration settings, running the project setup scripts to populate the database, calibrating model parameters using observed discharge, and reconstructing monthly discharge for the entire historical period. The resulting time series and flow-duration curves can be used for hydrological assessment and comparative basin analysis.

---

## Availability

IUH NASH LinearRes is released as open-source software under the MIT license. The source code, documentation, and example data are available at:

https://github.com/alessandroamaranto/q_rec_nash_iuh
