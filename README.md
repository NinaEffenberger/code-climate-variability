# Uncertainty in wind and solar projections depends on global and regional climate models

## Description
This repository contains the code and processing pipelines for the paper **"Uncertainty in wind and solar projections depends on global and regional climate models"**. 

The project aims to quantify the relative contribution of RCMs and GCMs to the projected uncertainty of wind and solar radiation data. 
---

## Installation
To recreate the environment used in this study, use the provided `environment.yml` file:

```bash
# Clone the repository
git clone https://github.com/NinaEffenberger/code-energy-droughts
cd code-energy-droughts

# Create the conda environment
conda env create -f environment.yml

# Activate the environment
conda evaluation
```

## Project structure
```
├── data/               # Put the raw data here
├── download_data/      # Data pre-processing and re-gridding
├── plot/               # PDFs of plots
├── plotting/           # Code for plotting
├── plotting_data/      # Data for plotting
├── src/                # Code to generate plotting_data
├── environment.yml     # Conda environment definition
├── README.md           # Project documentation
└── requirements.txt    # Required packages

```
## Usage
Plotting: To reproduce the paper plots, run the code in the `plotting/` directory. All code for plotting is ready to use as the plotting data is in `plotting_data/`.

Results: For full transparency, this repository includes the complete processing pipeline used to generate the intermediate datasets required for plotting. The large original datasets are open-source and can be downloaded from the ESGF datanode and ERA5 land can be downloaded from Copernicus. Please contact the authors if you require further details.

## Citation
If you use this code or our findings, please cite:

Effenberger, N., & Knutti, R. (2026). Uncertainty in wind and solar projections depends on global and regional climate models. arXiv preprint arXiv:2603.20052.
