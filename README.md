# Fire Propagation Tree Toolkit (FPT) 
- Generating fire propagation tree graphs and fireplain data datasets from the fire growth model outputs

## Overview
This repository provides a toolkit for generating the fire propagation tree graphs and fireplain sets from the wildfire growth model outputs. The main script, `FPT.py`, processes the fire growth model outputs and generates the fire propagation tree graphs.

## Citation Notice
Yemshanov, D., Liu, N., Neilson, E., Thompson, D., Koch F. In review.  A graph-based optimization framework for firebreak planning in wildfire-prone landscapes. Ecological Informatics.


## Installation
1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Place your input files in the `rawData/` folder. The required files include:
   - ESRI shapefile with hexagons identifying the nodes-potential locations in the fire spread network (e.g.`hexagon400ha_cropped.shp` with the corresponding .shx, .dbf and other attribute files)
   - Text outputs and raw files generated with the BurnP3 fire growth model, e.g.`_BI.csv`, `_ROSRaw.csv`, `_FIRaw.csv`, `stats_.csv`, `bpmap_.asc`
2. Run the main script:
   ```bash
   python FPT.py
   ```
3. Outputs will be saved in the `output/` folder.

## Folder Structure
```
rawData/   # Input files
output/    # Output files
FPT.py     # Main analysis script
requirements.txt
README.md
```

## About `postbp`
- The code uses the postbp library - an open-source Python code for post-processing wildfire model outputs (see documentation in [https://nliu-cfs.github.io/postbp] https://nliu-cfs.github.io/postbp)
- The postbp describption can be found in Liu, N., Yemshanov, D., Parisien, M.-A., et al. (2024). PostBP: A Python library to analyze outputs from wildfire growth models. MethodsX, 13, 102816. DOI:10.1016/j.mex.2024.102816
- The library can be installed via pip: `pip install postbp`

## Contributing
Contributions, bug reports, and suggestions are welcome! Please open an issue or pull request.

## License
This project is licensed under the MIT License.

## Contact
For questions or collaboration, please contact the repository maintainer or open an issue. 
