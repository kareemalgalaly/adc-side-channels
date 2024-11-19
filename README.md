# SingleSlopeADC

## Organization
```
analog
  adc/adc.cir
  test
  lib
digital
  tb
  design
build
synth
Makefile
```

## Tools Used
- ngspice
- verilator
- yosys
- x-server (XQuartz on Mac)
- python
  - pytorch

## Make Commands

### Synthesize module
`make control_v0.synth`

### Simulate adc with given module verilog
`make control_v0.adcsim`
