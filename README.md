# CSAW ESC 2025 Final FossilizedPluto

This repo contains my solutions, relevant code and documentation for my final round submission to **CSAW Embedded Security Challenge, 2025**. 
- **Team name**: FossilizedPluto
- **Member**: Daksh Pandey
- **Supervisor**: Dr. Sparsh Mittal
- **College**: IIT Roorkee

## Repository Structure

```
fossilized_pluto_esc25/
├── solutions/         # Challenge solutions
│   ├── set1/          # Beginner challenges (timing, power, glitching)
│   ├── set2/          # Intermediate challenges (DPA, CPA)
│   └── set3/          # Advanced challenges (timing oracle, advanced CPA)
├── challenges/        # Target firmware (C source + HEX binaries)
├── reports/           # Qualification and final round reports
└── ai_opt/            # AI/ML optimizations
    ├── llm_attack_assistant/  # LLM-powered attack discovery
    ├── attacks/       # ML-enhanced attack implementations
    └── mitigations/   # LLM patches + anomaly detection
```

## Challenges (8 Total)

### Set 1: Timing, Power, and Fault Attacks
- **Gatekeeper1/2**: Timing side-channel password recovery (`gk1{l0g1npwn}`, `gk1{l0g1npwn}wlb4`)
- **Sorters Song**: Power analysis on sorting algorithm (`ss1{y0u_g0t_it_br0!}`, `ss2{!AEGILOPS_chimps`)
- **Critical Calculation**: Voltage glitching loop corruption (`cc1{C0RRUPT3D_C4LCUL4T10N}`)

### Set 2: Cryptographic Power Analysis
- **Hyperspace**: CPA on AES operations (`ESC{21hYP35TrEEt}`)
- **Dark Gatekeeper**: DPA on XOR operations (`ESC{J0lt_Th3_G473}`)
- **Ghost Blood**: Advanced CPA on ChaCha20 ROTL operations

### Set 3: Advanced Side-Channels
- **Echoes**: Timing oracle on sorting (`eoc{th3yreC00ked}`)
- **Alchemist**: Advanced CPA with trace alignment (`a1c{Wh1teDragonT}`)

Each challenge directory contains:
- `README.md` - Vulnerability analysis and flag
- `attack.py` - Attack implementation
- `analysis.py` - Signal/trace analysis

## AI/ML Optimizations

### LLM Attack Assistant (`ai_opt/llm_attack_assistant/`)

Automated vulnerability discovery and attack generation using LLMs (Claude):
- **trace_analyzer.py** - Analyzes traces and queries LLM for vulnerabilities
- **attack_generator.py** - Generates ChipWhisperer attack code from analysis
- **iterative_refiner.py** - Executes and refines code until successful
- **api_templates.py** - Pre-built templates for correct API usage
- **main.py** - Complete pipeline orchestration

Key innovation: Discovery from raw traces, not just code generation.

### Enhanced Attacks (`ai_opt/attacks/`)

**echoes_ml_oracle**: Random Forest classifier replaces threshold-based oracle
**dark_gatekeeper_nn**: Deep Neural Network for direct byte prediction
**hyperspace_cpa_ml**: Gradient boosting for correlation prediction
**critical_calc_rl**: Q-learning for glitch parameter optimization

### Mitigations (`ai_opt/mitigations/`)

#### LLM-Generated Patches (`llm_patches/`)
AI-assisted security patches for all 8 challenges:
- Constant-time operations
- Boolean masking (first/second-order)
- Operation shuffling
- Random delays
- Triple Modular Redundancy
- XOR blinding
- Clock jitter injection

Each challenge has paired `.md` (analysis) and `.c` (patch) files.

#### ML Anomaly Detection (`anomaly_detector/`)
Real-time attack detection using Isolation Forest classifier:
- `train_detector.py` - Train on normal vs attack patterns
- `monitor_realtime.py` - Deploy with countermeasures

## Hardware Platform

- **Target**: ChipWhisperer NANO
- **MCU**: STM32F0 (ARM Cortex-M0)
- **Firmware**: 8 HEX binaries in `challenges/`

## Attack Techniques

- Timing side-channel analysis
- Differential Power Analysis (DPA)
- Correlation Power Analysis (CPA)
- Voltage glitching / fault injection
- Binary search oracles
- Trace alignment and synchronization

## ML Techniques

- **Supervised Learning**: Random Forest, DNNs, Gradient Boosting
- **Reinforcement Learning**: Q-learning with epsilon-greedy exploration
- **Anomaly Detection**: Isolation Forest for intrusion detection
- **LLM Assistance**: Automated secure code generation

## Dependencies

```bash
pip install chipwhisperer numpy scikit-learn tensorflow matplotlib scipy tqdm anthropic
```

## Usage

### Run Attack
```bash
cd solutions/set1/gatekeeper1
python attack.py
```

### Run Analysis
```bash
python analysis.py
```

### Train ML Models
```bash
cd ai_opt/attacks/echoes_ml_oracle
python train_classifier.py
python attack_with_ml.py
```

### Deploy Mitigations
```bash
cd ai_opt/mitigations/anomaly_detector
python train_detector.py
python monitor_realtime.py
```

### LLM Attack Discovery
```bash
cd ai_opt/llm_attack_assistant
export ANTHROPIC_API_KEY='your-key-here'
python main.py traces.npy challenge_name firmware.hex -o attack.py
```

## Notes

- All implementations are educational/research purposes
- Mitigations require security review before production use
- Models trained on specific hardware (may need retraining)
- Firmware source code available in `challenges/`

