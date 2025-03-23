# STEP to G-code Converter - Quick Start Guide

## Core Functionality

This tool can perform the following conversions:
1. STEP Files → FANUC G-code
2. DWG Files → STEP Files → FANUC G-code

## Environment Setup

Ensure your system has Python 3.6+ and the following dependencies:
```bash
# Activate virtual environment (if available)
source gcode_env/bin/activate

# Install dependencies
pip install numpy matplotlib
```

## Getting Started

### Method 1: Direct STEP File Conversion (Recommended)

If you already have STEP files, use the NumPy optimized version for best results:

```bash
python step_to_fanuc_numpy.py "your_file.stp" -o "output/output_file.nc" -f 600 -s 15 -d 0.5 -v
```

Parameter explanation:
- `-f 600`: Cutting feed rate (mm/min)
- `-s 15`: Safety height (mm)
- `-d 0.5`: Cutting depth (mm)
- `-v`: Generate visualization charts

### Method 2: Starting with DWG Files

If you only have DWG files, first convert to STEP:

```bash
# Step 1: DWG to STEP
python advanced_dwg_to_step.py "your_file.dwg" --type busbar

# Step 2: STEP to G-code
python step_to_fanuc_numpy.py "generated_step_file.stp" -o "output/output_file.nc" -f 600 -s 15 -d 0.5 -v
```

Part type options:
- `busbar`: Standard busbar
- `front_busbar`: Front busbar
- `rear_busbar`: Rear busbar

## Common Usage Examples

### Example 1: Processing Rear Busbar

```bash
# If you have a STEP file
python step_to_fanuc_numpy.py "INTER BUSBAR REAR-1.STP" -o "output/rear_busbar.nc" -f 600 -s 15 -d 0.5 -v

# If you only have a DWG file
python advanced_dwg_to_step.py "TNGA_INTER_BUSBAR_REAR-1.dwg" --type rear_busbar
python step_to_fanuc_numpy.py "TNGA_INTER_BUSBAR_REAR-1.stp" -o "output/rear_busbar.nc" -f 600 -s 15 -d 0.5 -v
```

### Example 2: Using Lightweight Converter (For Low-Spec Computers)

```bash
python fanuc_stp_to_gcode_no_numpy.py "your_file.stp" -o "output/lightweight_output.nc" -f 600 -s 15 -d 0.5
```

## Output Files

1. G-code files are saved in the `output` directory
2. Visualization charts are saved in the `plots` directory:
   - 3D model view (3d_model.png)
   - Contour view (contours.png) 
   - XY projection (xy_projection.png)

## Pre-Use Check

Run the dependency check tool to ensure correct environment setup:
```bash
python fix_dependencies.py
```

## Common Issues

1. **Missing Dependencies**: Run `pip install numpy matplotlib` to install missing libraries
2. **File Not Found**: Ensure the file path is correct, including file extensions
3. **Insufficient Geometric Information**: Use the advanced DWG converter to create standardized STEP files

## Getting Help

View command-line parameter help:
```bash
python step_to_fanuc_numpy.py --help
python advanced_dwg_to_step.py --help
```

For complete documentation, refer to `User_Manual.md` 