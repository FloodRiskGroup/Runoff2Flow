---
title: "Runoff2Flow: A reproducible framework for monthly river discharge reconstruction using IUH Nash and linear reservoir modeling"
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

Reliable river discharge time series are essential for hydrological analysis, water resources management, and climate impact assessment. However, many river basins lack continuous long-term discharge observations, particularly when analyses are conducted at monthly temporal resolution or over historical periods. **Runoff2Flow** is an open-source, configuration-driven framework for reconstructing monthly river discharge using an Instantaneous Unit Hydrograph (IUH) Nash model combined with a linear reservoir representation of baseflow. The software integrates surface runoff and groundwater recharge inputs with observed discharge data, calibrates model parameters using a genetic algorithm, and reconstructs discharge over extended historical periods. A database-centered architecture based on SQLite ensures reproducible data handling, while script-based workflows support calibration, validation, and flow-duration curve analysis. The framework is intended for hydrologists and environmental scientists working in data-scarce or partially observed basins.

---

## Statement of need

Continuous river discharge records are essential for water resources assessment, hydrological analysis, and climate change impact studies [@depetris2021importance]. However, long and uninterrupted discharge observations remain unavailable for many river basins due to sparse monitoring networks, historical data gaps, and changes in measurement practices [@lin2024estimating]. These limitations are particularly relevant for large-scale and long-term studies, where consistent discharge measurements are often incomplete or entirely absent. At the same time, the availability of spatially continuous runoff and groundwater recharge products derived from reanalysis, land-surface models, and satellite observations [@era5land2019; @gldas2_monthly_2.0; @ispra_bigbang, @wu2024hydrological] has increased substantially [@naz20203; naz2019improving]. These datasets provide long, internally consistent time series of hydrological fluxes, but they cannot be directly used for river discharge analyses without an explicit representation of basin-scale hydrological response. Converting runoff to discharge at a monthly temporal resolution is paramount [@camici2021synergy], especially for applications such as drought characterization [@mckee1993relationship], ow-flow analysis, and climate change impact assessment [@amaranto2025unravelling], where monthly aggregation captures dominant hydro-climatic signals while reducing the influence of short-term variability. 

**Runoff2Flow** addresses this gap by providing a lightweight and reproducible framework specifically designed for monthly river discharge reconstruction using aggregated climate inputs. The software implements an IUH Nash cascade [@Nash1957] coupled with a linear reservoir model to represent basin response and baseflow dynamics [@Eckhardt2005], and employs a genetic algorithm for parameter calibration across multiple objective functions [@Goldberg1989; @Gupta2009]. The software is intended for applications where discharge observations are sparse or incomplete, including comparative basin studies, long-term historical reconstructions, and sensitivity analyses. 

---

## Software description

### Architecture and workflow

The framework is organized into a two-phase workflow. The first phase focuses on project setup, including watershed averaging of climate inputs, loading of observed discharge data, and creation of a SQLite database to store all time series. The second phase performs model calibration, validation, and simulation, including genetic algorithm optimization, full-period discharge reconstruction, and flow-duration curve analysis.

All workflows are executed through standalone Python scripts, with model parameters and execution options controlled via INI configuration files. This design minimizes hidden dependencies and facilitates reproducible experimentation without modifying source code. Key design choices include the use of plain-text configuration files, avoidance of hidden state within objects, and explicit database persistence of all intermediate and final results. These choices were made to facilitate traceability, reproducibility, and long-term reuse of reconstructed discharge datasets.

Runoff2Flow should be understood not as a new hydrological model formulation, but as a reproducible computational framework that integrates established hydrological concepts into a transparent, script-driven workflow.

### Hydrological model

The core hydrological model is based on the Instantaneous Unit Hydrograph (IUH) Nash formulation [@Nash1957], representing basin response as a cascade of linear reservoirs. This approach has proven effective for monthly-scale discharge simulations and provides a parsimonious parameterization suitable for data-limited basins. A separate linear reservoir is used to model baseflow contributions driven by groundwater recharge, consistent with baseflow separation methodologies [@Eckhardt2005]. The model operates at monthly temporal resolution and is implemented as a lumped basin-scale representation.

Missing or invalid observations are explicitly encoded using negative values, allowing continuous data periods to be identified programmatically for calibration and validation [@Klemes1986; @Wagener2007].

### Calibration and analysis

Model parameters are calibrated using a custom genetic algorithm implementation that supports multiple objective functions: Nash–Sutcliffe efficiency [@NashSutcliffe1970], root mean square error, and mean absolute error [@Moriasi2007]. Calibration and validation periods are selected automatically based on continuous data availability [@Klemes1986]. After calibration, the model reconstructs discharge over the full historical period and computes flow-duration curves for frequency analysis [@Harman2009]. The multi-objective function approach allows users to select calibration criteria based on specific applications and data characteristics.

---

## Example use case

The repository includes example climate, discharge, and geospatial datasets that allow users to execute the full workflow without external data downloads. A typical use case involves configuring basin parameters and calibration settings, running the project setup scripts to populate the database, calibrating model parameters using observed discharge, and reconstructing monthly discharge for the entire historical period. The resulting time series and flow-duration curves can be used for hydrological assessment and comparative basin analysis.

Typical outputs include reconstructed monthly discharge time series, calibrated model parameters, performance metrics for calibration and validation periods, and flow-duration curves derived from the reconstructed record. These outputs can be directly used in water resources assessment, drought and low-flow analysis, or comparative basin studies.

---

## Availability

Runoff2Flow is released as open-source software under the MIT license. The source code, documentation, and example data are available at:

https://github.com/FloodRiskGroup/Runoff2Flow

# AI usage disclosure

During the preparation of this work the authors used ChatGPT to improve the readability of some paragraphs and to provide feedbacks about the quality of the documentation. After using this tool/service, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication. ChatGPT was also used to outline the tests. No AI tools were instead employed to write the software.

# Acknowledgements

This work has been financed by the Research Fund for the Italian Electrical System under the Three-Year Research Plan 2025-2027 (MASE, Decree n.388 of November 6th, 2024), in compliance with the Decree of April 12th, 2024. 

# References