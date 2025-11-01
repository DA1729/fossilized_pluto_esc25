# Critical Calculation - Voltage Glitching Attack

## Challenge Overview

This challenge involves performing a voltage glitch attack on an STM32F0 microcontroller executing a critical calculation loop. The objective is to induce a controlled fault that corrupts the loop iteration count, bypassing the normal diagnostic response to reveal a hidden flag.

## Setup

- **Target Platform**: STM32F0 series MCU (ChipWhisperer Nano)
- **Firmware**: `criticalCalculation-CWNANO.hex`
- **Attack Type**: Voltage glitching using ChipWhisperer
- **Communication**: SimpleSerial protocol

## Approach

### 1. Analysis Phase (`analysis.py`)

The analysis script captures power traces during normal execution to understand the device's power characteristics:

- Captures 20 power traces during normal operation
- Generates visualization plots:
  - All traces overlay
  - Average power trace
  - First 10 individual traces
- Helps identify timing windows for glitch injection

### 2. Attack Phase (`attack.py`)

The attack implements an adaptive two-stage glitch parameter search:

**Stage 1: Coarse Scan**
- Wide parameter ranges with few samples per setting
- Quickly identifies promising regions
- Parameters: `repeat=[1-10]`, `ext_offset=[1-200]`, step=5, samples=3

**Stage 2: Fine Scan**
- Focused scan on identified regions
- More samples for reliability
- Parameters: `repeat=[5-15]`, `ext_offset=[100-150]`, step=1, samples=10

**Key Features:**
- Early termination on flag discovery
- Automatic reset handling and retry logic
- Progress logging every 10 parameter combinations
- Abort mechanism for repeated device resets

## Results

- **Flag**: `cc1{C0RRUPT3D_C4LCUL4T10N}`
- **Successful Glitch Parameters**:
  - `repeat=12`
  - `ext_offset=100`

## Attack Methodology

1. The device executes a loop with integrity checks
2. Voltage glitch corrupts the loop counter
3. Diagnostic check fails to detect the corruption
4. Device returns the hidden flag instead of "DIAGNOSTIC_OK"

## Key Insights

- **Precise Timing**: Voltage glitching requires accurate parameter tuning to induce controlled faults without crashing the device
- **Adaptive Search**: Two-stage scanning dramatically reduces search time compared to exhaustive scanning
- **Automation**: Integration with ChipWhisperer's hardware/software tools enables efficient fault injection research

## Mitigation Strategies

1. **Redundant Checks**: Implement multiple independent integrity checks
2. **Diverse Calculations**: Use different calculation methods for verification
3. **Glitch Detection**: Monitor power supply variations
4. **Code Obfuscation**: Increase complexity of critical loops
5. **Hardware Countermeasures**: Add filtering capacitors and power supply monitoring

## Usage

### Run Analysis:
```bash
python analysis.py
```
Generates power trace plots for analysis.

### Run Attack:
```bash
python attack.py
```
Executes the adaptive glitch search and retrieves the flag.

## Dependencies

- ChipWhisperer toolkit
- NumPy
- Matplotlib
- tqdm
