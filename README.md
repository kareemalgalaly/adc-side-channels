# SingleSlopeADC

- [ ] This document requires significant updating

## Organization
```txt
analog
digital
  tb
  design
    top
    unprotected
attack/cnn
script
build
synth
Makefile
```

## Tools Used
- ngspice
- verilator
- yosys
- x-server (XQuartz or Xpra on Mac)
- python
  - pytorch

## Make Commands
This section is far outdated. Most analog designs come with a run.sh

```bash
make control_v0.synth  # Synthesize module
make control_v0.adcsim # Simulate adc with given module verilog
```

## Conference Paper
### Objective

1. Combine analog and digital designs into a joint attack (1 pixel)
    a. Unprotected design
    a. Protected design (digital #3, analog random ramp for dummy)
    a. Protected design (digital #3, analog random ramp for both, requires digital resolve logic)
2. Try various attack techniques
3. Use better data splitting (markov datasets), including perhaps a validation dataset

::: info
**From Mooney's Slides**

- if a single pixel cannot be protected, then the protection of multiple pixels will likely be problematic
- if a single pixel can be protected, we can then proceed with perhaps similar techniques to protect large simultaneous samples of a realistic pixel array size
:::

### Required Work 

| #  | Description                                  | Engineering Effort | Time Effort |
|----|----------------------------------------------|-----------------|-----------------|
| 1. | Setup multi-trace CNN attack                 | Medium          | ~ 1 wk          |
| 2. | Implement digital logic for random ramp      | High            | ~ 1-2 wks       |
| 3. | TT simulation for training                   | Low             | ???             |
| 5. | Corner simulations for test dataset          | Low             | ???             |
| 6. | Markov-based simulations for test dataset    | Low-Medium      | ???             |
| 7. | Sweep CNN trace scale                        | Low-Medium      | ???             |

### Optional Work 
| #  | Description                                  | Engineering Effort | Time Effort |
|----|----------------------------------------------|-----------------|-----------------|
| 1. | Place and route digital logic                | High            | 2+ wks          |
| 2. | Setup different types of CNN attack          | High            | 3+ wks          |
| 3. | Additional analog updates? (e.g. IDAC)       | ???             | ???             |
| 4. | Explore additional analog protections?       | ???             | ???             |
| 5. | Understand vanishing gradient issue (multipix) | High          | ???             |
| 6. | Multipixel attack                            | High            | ???             |


::: {.info .warn}
- assuming pixels with wide dynamic range
- random ramp that reaches 255 early or never reaches may be a point of information leakage
:::
