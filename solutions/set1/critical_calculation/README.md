# Critical Calculation - Voltage Glitching Attack

## Vulnerability

Voltage glitch attack on STM32F0 microcontroller corrupts loop iteration count, bypassing integrity checks to reveal hidden flag.

## Attack Strategy

**Two-stage adaptive search:**

1. **Coarse Scan**: Wide parameter ranges (`repeat=[1-10]`, `ext_offset=[1-200]`, step=5) to identify promising regions
2. **Fine Scan**: Focused scan on identified regions (`repeat=[5-15]`, `ext_offset=[100-150]`, step=1) for reliability

**Successful Parameters**: `repeat=12`, `ext_offset=100`

## Flag

**cc1{C0RRUPT3D_C4LCUL4T10N}**

## Mitigation

- Redundant integrity checks
- Diverse calculation methods for verification
- Glitch detection via power supply monitoring
- Hardware countermeasures (filtering capacitors)
- Code obfuscation
