# Fire Propagation Tree Toolkit (FPT)

## Overview
This repository provides a toolkit for post-processing and analyzing outputs from wildfire growth models, with a focus on the Canadian Burn-P3 model. The main script, `FPT.py`, processes simulation outputs, constructs fire spread graphs, and generates scenario-based outputs for further analysis.

## Citation Notice
**If you use this code or its outputs in your research, please cite our journal article. **

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
3. Install the `postbp` package (required):
   ```bash
   pip install postbp
   ```
   For more information, see the [postbp GitHub page](https://github.com/nliu-cfs/postbp).

## Usage
1. Place your input files in the `rawData/` folder. Required files include:
   - hexagon shapefile, e.g.`hexagon400ha_cropped.shp` (+ associated .shx, .dbf, etc.)
   - BurnP3 generated files, e.g.`_BI.csv`, `_ROSRaw.csv`, `_FIRaw.csv`, `stats_.csv`, `bpmap_.asc`
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
- `postbp` is an open-source Python library for post-processing wildfire model outputs.
- Documentation: [https://nliu-cfs.github.io/postbp](https://nliu-cfs.github.io/postbp)
- Install via pip: `pip install postbp`

## Citing This Work
If you use this toolkit, please cite:
> Liu, N., Yemshanov, D., Parisien, M.-A., et al. (2024). PostBP: A Python library to analyze outputs from wildfire growth models. MethodsX, 13, 102816. DOI:10.1016/j.mex.2024.102816

## Contributing
Contributions, bug reports, and suggestions are welcome! Please open an issue or pull request.

## License
This project is licensed under the MIT License.

## Contact
For questions or collaboration, please contact the repository maintainer or open an issue. 