# STEP to G-code Converter - Operation Demonstration Guide

This document helps you quickly master the STEP to G-code conversion tool through practical operation demonstrations.

## Demo 1: Processing STEP Files to Generate G-code

### Scenario
You have a STEP format part file "INTER BUSBAR REAR-1.STP" and need to generate G-code for a FANUC CNC machine.

### Operation Steps

1. **Confirm Environment Setup**
   ```bash
   # Activate virtual environment
   source gcode_env/bin/activate
   
   # Check dependencies
   python fix_dependencies.py
   ```

2. **Execute Conversion Command**
   ```bash
   python step_to_fanuc_numpy.py "INTER BUSBAR REAR-1.STP" -o "output/rear_busbar.nc" -f 600 -s 15 -d 0.5 -v
   ```

3. **Check Conversion Results**
   ```bash
   # View first 20 lines of G-code
   head -n 20 output/rear_busbar.nc
   
   # View generated visualization charts
   ls -la plots/
   ```

4. **Conversion Result Description**
   - G-code file: `output/rear_busbar.nc`
   - 3D model chart: `plots/3d_model.png`
   - Contour view: `plots/contours.png`
   - XY projection: `plots/xy_projection.png`

## Demo 2: DWG File to STEP to G-code

### Scenario
You have a DWG format front busbar file "TNGA_INTER_BUSBAR_FRONT-1.dwg" and need to ultimately generate G-code.

### Operation Steps

1. **Convert DWG to STEP**
   ```bash
   python advanced_dwg_to_step.py "TNGA_INTER_BUSBAR_FRONT-1.dwg" --type front_busbar
   ```
   Note: This command will generate STEP file "TNGA_INTER_BUSBAR_FRONT-1.stp"

2. **Convert STEP to G-code**
   ```bash
   python step_to_fanuc_numpy.py "TNGA_INTER_BUSBAR_FRONT-1.stp" -o "output/front_busbar.nc" -f 600 -s 15 -d 0.5 -v
   ```

3. **Confirm Conversion Results**
   ```bash
   # Check G-code file size
   ls -lh output/front_busbar.nc
   
   # View toolpath visualization
   open plots/xy_projection.png  # Mac system
   # or: xdg-open plots/xy_projection.png  # Linux system
   ```

## Demo 3: Using Lightweight Converter for Low-Spec Computers

### Scenario
Your computer has low specifications and you need to use a lightweight converter that doesn't depend on NumPy to process STEP files.

### Operation Steps

1. **Execute Lightweight Conversion**
   ```bash
   python fanuc_stp_to_gcode_no_numpy.py "INTER BUSBAR REAR-1.STP" -o "output/lightweight_output.nc" -f 600 -s 15 -d 0.5
   ```

2. **Compare Conversion Results**
   ```bash
   # Compare file sizes
   ls -lh output/lightweight_output.nc output/rear_busbar.nc
   
   # Check G-code content differences
   diff <(head -n 20 output/lightweight_output.nc) <(head -n 20 output/rear_busbar.nc)
   ```

3. **Notes**
   - Lightweight version is faster but has lower path optimization
   - Does not support generating visualization charts
   - Suitable for scenarios requiring quick conversion

## Demo 4: Batch Processing Multiple Files

### Scenario
You need to batch process multiple STEP files to generate corresponding G-code.

### Operation Steps

1. **Create Batch Processing Script**
   Create file `batch_process.sh`:
   ```bash
   #!/bin/bash
   
   # Find all STEP files and process them
   for file in *.STP *.stp; do
     if [ -f "$file" ]; then
       echo "Processing file: $file"
       output_name="output/$(basename "$file" | sed 's/\.[Ss][Tt][Pp]$/_output.nc/')"
       python step_to_fanuc_numpy.py "$file" -o "$output_name" -f 600 -s 15 -d 0.5 -v
     fi
   done
   
   echo "Batch processing complete!"
   ```

2. **Add Execution Permission and Run**
   ```bash
   chmod +x batch_process.sh
   ./batch_process.sh
   ```

3. **Check Processing Results**
   ```bash
   ls -lh output/
   ```

## Common Issues and Solutions

### Issue 1: STEP File Parsing Error
```
Error: Unable to extract sufficient geometric information from STEP file
```

**Solutions:**
- Ensure the STEP file contains valid geometric information
- Try using the advanced DWG converter to regenerate the STEP file
- Check if the STEP file format meets the standard

### Issue 2: Missing Dependency Modules
```
ModuleNotFoundError: No module named 'numpy'
```

**Solution:**
```bash
pip install numpy matplotlib
```

### Issue 3: Output File is Empty or Abnormal
**Solutions:**
- Check if the input file contains valid geometric data
- Try using a smaller step size parameter `-s 10` to increase precision
- Verify command parameters are correct

## Summary

Through the above four demonstrations, you should have understood the basic usage of the STEP to G-code conversion tool. Based on your actual needs, you can choose the appropriate conversion method:

1. High-precision NumPy version - Suitable for scenarios requiring path optimization and visualization
2. Lightweight non-NumPy version - Suitable for low-spec computers or simple conversions
3. Direct DWG conversion - Suitable for scenarios where only CAD drawings are available

Please refer to `User_Manual.md` for more detailed parameter descriptions and advanced features. 