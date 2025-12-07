# 3D LUT Patch Converter

A simple, interactive Python tool to rescale/convert RGB color patch CSVs between different bit-depths and signal ranges. Designed for color science workflows and 3D LUT generation.

## Features

- **Bidirectional Conversion**: Convert from 8-bit to 10-bit, or 10-bit back to 8-bit.
- **Range Support**:
  - Full Range (e.g., 0-255, 0-1023)
  - Legal/Limited Range (e.g., 16-235, 64-940)
  - Custom Range (User-defined Min/Max)
- **Interactive CLI**: Simple step-by-step prompts to guide your conversion.
- **Batch Friendly**: Works with standard CSV files containing `R`, `G`, `B` columns.

## Requirements

- Python 3.x
- pandas
- numpy

```bash
pip install pandas numpy
