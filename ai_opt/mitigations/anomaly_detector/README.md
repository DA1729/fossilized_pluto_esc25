# ML-Based Anomaly Detection

Real-time attack detection system using Isolation Forest classifier to identify malicious patterns.

## Components

### train_detector.py
Trains Isolation Forest classifier on normal vs attack behavior patterns.

**Dataset**: 500 normal traces + 500 simulated attack traces

**Features**:
- Request timing patterns
- Query frequency
- Parameter distributions (password composition, positions)
- Response patterns

**Model**: Isolation Forest (100 estimators, 10% contamination)

**Output**: `anomaly_detector.pkl` (detector + scaler)

### monitor_realtime.py
Deploys trained model for real-time monitoring and threat response.

**Detection Strategy**:
- Moving window (100 requests)
- Anomaly counter with threshold (5+ anomalies trigger alert)
- Continuous monitoring loop

**Countermeasures**:
- Rate limiting
- Temporary account lockout
- Forensic logging
- Adaptive defense parameter adjustment

## Usage

```bash
python train_detector.py      # Train model
python monitor_realtime.py    # Deploy monitoring
```

## Notes

- Trained on CWNANO (ChipWhisperer NANO) platform
- Models specific to hardware setup
- Provides detection layer complementing LLM patches
