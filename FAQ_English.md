# STEP to G-code Converter - Frequently Asked Questions

## Basic Questions

### Q1: How do I choose the right converter version?
**Answer**: 
- If your computer has good performance and you need path optimization and visualization, choose the NumPy version (`step_to_fanuc_numpy.py`)
- If your computer has limited performance or you only need simple conversion, choose the lightweight version (`fanuc_stp_to_gcode_no_numpy.py`)
- If you only have DWG files, first use `advanced_dwg_to_step.py` to convert to STEP, then process with the above tools

### Q2: What do the various command-line parameters mean?
**Answer**:
- `-o, --output`: Specify the output G-code file path
- `-f, --feed_rate`: Specify the cutting feed rate (mm/min)
- `-s, --safety_height`: Specify the safety height (mm)
- `-d, --depth`: Specify the cutting depth (mm)
- `-v, --visualize`: Enable visualization (only supported by NumPy version)
- `--type`: Specify the part type (used when converting DWG)

### Q3: What are the differences between the part types for conversion?
**Answer**:
- `busbar`: Standard busbar, processed using general parameters
- `front_busbar`: Front busbar, optimizes the front connection part
- `rear_busbar`: Rear busbar, optimizes the rear connection part

## Installation-Related Issues

### Q4: How do I fix dependency installation problems?
**Answer**:
```bash
# Method 1: Direct installation using pip
pip install numpy matplotlib

# Method 2: Installation using requirements file
pip install -r requirements.txt

# Method 3: Resolving permission issues
pip install --user numpy matplotlib
```

### Q5: Why do I still get module missing errors after installing dependencies?
**Answer**:
This may be due to Python environment issues. Please check:
1. Whether the correct virtual environment is activated
2. Whether your Python version is compatible (3.6+ recommended)
3. Try restarting the terminal or IDE
4. Check if the module installation location is in the Python path

### Q6: How do I resolve permission errors when installing on macOS?
**Answer**:
```bash
# Install using sudo (requires administrator password)
sudo pip install numpy matplotlib

# Or use the --user option to install to the user directory
pip install --user numpy matplotlib

# Or install Python using Homebrew then install dependencies
brew install python
pip3 install numpy matplotlib
```

## File Conversion Issues

### Q7: Why can't my STEP file be parsed correctly?
**Answer**:
Possible reasons include:
1. The STEP file format is non-standard or damaged
2. The STEP file does not contain valid geometric information
3. The unit settings in the STEP file do not match program expectations

Solutions:
- Use the advanced DWG converter to regenerate the STEP file
- Try re-exporting the STEP file in CAD software, ensuring all geometric information is included
- Check if the file is complete, try to repair damaged files

### Q8: I'm getting a "Cannot recognize part type" error when converting DWG files?
**Answer**:
Please ensure:
1. You're explicitly specifying the part type using the `--type` parameter
2. The DWG filename follows the naming convention
3. The DWG file contains valid geometric information
4. Try using the latest version of the conversion tool

### Q9: What should I do if NaN values appear in the generated G-code?
**Answer**:
NaN values are usually caused by mathematical errors during calculation. Solutions:
1. Check if there are abnormal geometric shapes in the STEP file
2. Add parameter `--tolerance 0.001` to increase precision
3. Update to the latest version of the conversion tool
4. Add additional geometric constraints around the problem area

## Performance Issues

### Q10: How do I resolve insufficient memory when converting large STEP files?
**Answer**:
1. Use the lightweight converter (`fanuc_stp_to_gcode_no_numpy.py`)
2. Increase system virtual memory
3. Split large files into multiple smaller files for separate processing
4. Use parameter `--optimize memory` to reduce memory usage (advanced version only)

### Q11: Processing is too slow, how can I optimize?
**Answer**:
1. Reduce model precision using parameter `--simplify 0.1`
2. Don't use visualization features (remove the `-v` parameter)
3. Close other CPU-intensive applications
4. For very complex models, consider using batch scripts to run during night or low-load times

### Q12: The generated G-code file is too large, how can I reduce it?
**Answer**:
1. Use a larger tolerance value: `--tolerance 0.01`
2. Reduce path point density: `--point_density 0.5`
3. Use compression option: `--compress`
4. For post-processing, you can use external tools to compress G-code files

## Output Quality Issues

### Q13: The generated contours are incomplete, how do I fix this?
**Answer**:
1. Check if there are broken contours in the STEP file
2. Lower precision parameter: `--tolerance 0.001`
3. Use the `--close_contours` option to automatically close contours
4. Fix the model in the original CAD and re-export

### Q14: Are differences in G-code generated by different converter versions normal?
**Answer**:
Yes, this is normal. Different versions of converters use different algorithms:
- NumPy version uses more advanced path optimization algorithms
- Lightweight version prioritizes speed and memory usage
- You can use the `diff` command to compare outputs and assess the importance of differences

### Q15: Visualization charts display incorrectly or are missing?
**Answer**:
1. Ensure matplotlib is installed and the version is compatible
2. Check if there is enough disk space to save charts
3. Try a different backend: `export MPLBACKEND=Agg`
4. Update matplotlib: `pip install --upgrade matplotlib`

## Batch Processing Issues

### Q16: How do I batch process multiple STEP files?
**Answer**:
Refer to "Demo 4" in `Operation_Demos_English.md`, create and run a batch script:
```bash
#!/bin/bash
for file in *.STP *.stp; do
  if [ -f "$file" ]; then
    output_name="output/$(basename "$file" | sed 's/\.[Ss][Tt][Pp]$/_output.nc/')"
    python step_to_fanuc_numpy.py "$file" -o "$output_name" -f 600 -s 15 -d 0.5 -v
  fi
done
```

### Q17: How do I set specific parameters for different files in batch processing?
**Answer**:
You can create a configuration file (such as config.json) containing specific parameters for each file:
```json
{
  "file1.stp": {"feed_rate": 800, "depth": 0.3},
  "file2.stp": {"feed_rate": 600, "depth": 0.5}
}
```
Then read this configuration file in the batch script to apply specific parameters.

### Q18: How do I skip already processed files during batch processing?
**Answer**:
Modify the batch script to check if the output file already exists:
```bash
#!/bin/bash
for file in *.STP *.stp; do
  if [ -f "$file" ]; then
    output_name="output/$(basename "$file" | sed 's/\.[Ss][Tt][Pp]$/_output.nc/')"
    if [ ! -f "$output_name" ]; then
      echo "Processing: $file"
      python step_to_fanuc_numpy.py "$file" -o "$output_name" -f 600 -s 15 -d 0.5 -v
    else
      echo "Skipping existing: $output_name"
    fi
  fi
done
```

## Other Issues

### Q19: How do I customize G-code header and footer code?
**Answer**:
Create custom template files:
1. Create `templates/header.txt` containing header code
2. Create `templates/footer.txt` containing footer code
3. Use parameters `--header templates/header.txt --footer templates/footer.txt`

### Q20: Does the tool support G-code formats for other CNC control systems?
**Answer**:
Currently, it mainly supports FANUC format, but other formats can be supported through:
1. Using the parameter `--format haas|siemens|mazak` (if supported)
2. Modifying the G-code generation part in the source code
3. Using post-processing scripts to convert FANUC format to other formats

### Q21: What are the future development plans for the project?
**Answer**:
1. Add support for more CNC control systems
2. Improve performance for processing large files
3. Add more visualization and simulation features
4. Develop a graphical user interface
5. Support multi-axis machining path generation

For more questions, please contact the development team or submit an issue in the project repository. 