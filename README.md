# SingleSlopeADC

This repo contains the designs and experiments used for the following papers:

[C. Körpe, K. Ahmad, E. Öztürk, K. Tihaiya, R. Tran, H. Yang, J. Yang, G. Dündar, V. Mooney and K. Ozanoglu, "A Side-Channel Attack-Resilient Single-Slope ADC for Image Sensor Applications," 21st International Conference on Synthesis, Modeling, Analysis and Simulation Methods, and Applications to Circuit Design (SMACD'25), July 2025.](https://xplorestaging.ieee.org/document/11092095/)

[K. Ahmad, E. Öztürk, C. Körpe, H. Yang, J. Yang, K. Tihaiya, R. Tran, G. Dündar, V. Mooney and K. Ozanoglu, "Protection of the Digital Circuitry of a Single-Slope ADC Against Side-Channel Attacks," 2025 IEEE International Conference on Cyber Security and Resilience (CSR'25), August 2025.](https://xplorestaging.ieee.org/document/11130145)

## Tools Required
- ngspice (version 44 or later)
- verilator
- yosys
- x-server (XQuartz or Xpra on Mac)
- python (version 3.10 or later)
  - pytorch
- bash

Tools have been tested on MacOS Sequoia (arm), Debian 12 Bookwork (amd64), and Fedora 42 (amd64). Shell scripts are written for bash.

## Toolchain Setup (Spice Simulations and CNN Attack)

1. Install ngspice 
2. Clone efabless skywater PDK libraries
    - [https://github.com/efabless/skywater-pdk-libs-sky130_fd_pr]()
    - [https://github.com/efabless/skywater-pdk-libs-sky130_fd_sc_hs]() 
3. Edit .spiceinit files (`analog/*/.spiceinit`) to point to cloned efabless repos
4. Edit Makefile PDK
6. Install python 3.10 or higher
7. Install all libraries in `requirements.txt`. 
   `pip install -r requirements.txt`

## Toolchain Setup (Digital Synthesis)

1. Install yosys
2. Clone skywater PDK library
    - [https://github.com/google/skywater-pdk]()
3. Run the following commands in skywater repo:
```bash
    SUBMODULE_VERSION=latest make submodules -j3 || make submodules -j1
    make timing
```
4. Clone efabless skywater PDK libraries
    - [https://github.com/efabless/skywater-pdk-libs-sky130_fd_pr]()
    - [https://github.com/efabless/skywater-pdk-libs-sky130_fd_sc_hs]() 
5. Edit the first three entries in the makefile:
```Makefile
    PDK_PROCESS_LIB	?= ${PATH_TO_EFABLESS_FD_PR_REPO}/models/sky130.lib.spice
    PDK_CELL_LIB 	?= ${PATH_TO_EFABLESS_FD_SC_HS_REPO}/cells
    PDK_LIBERTY     ?= ${PATH_TO_SKYWATER_REPO}/latest/timing/sky130_fd_sc_hs__tt_025C_1v50.lib
```

## Experiments (SMACD '25)

### Experiment 1: Unprotected

```bash
cd analog/analog_base
./gen_test.sh 1px
ngspice runme_1px_tt_xx_0.cir
ngspice runme_1px_tt_xm_0.cir
ngspice runme_1px_tt_xl_0.cir
mkdir -p ../outfiles
mv outfiles/* ../outfiles
```

The `demo.*cir` files run a small set of simulations and produce plots for viewing basic results.

### Experiment 2: Protected

```bash
cd analog/analog_base
./gen_test.sh tt1
./gen_test.sh tt2
./gen_test.sh ttl
./gen_test.sh sf
for runfile in $(ls | grep runme.*cir); do
    ngspice $runfile
done
mkdir -p ../outfiles
mv outfiles/* ../outfiles
```

The `demo.*cir` files run a small set of simulations and produce plots for viewing basic results.

### CNN Attack

```bash
cd attack/cnn
python regress.py --json smacd.json
```

Generates training plots and `run_results.csv` in `outfiles`.

Use `--help` for additional arguments

## Experiments (HACS  '25)

### Experiment 1 : Unprotected

```bash
cd analog/ece_1px
./gen_tests 1px
ngspice runme_1px_tt_x_0.cir
ngspice runme_1px_ss_x_0.cir
ngspice runme_1px_fs_x_0.cir
mkdir -p ../outfiles
mv outfiles/* ../outfiles
```

### Experiment 2 : Failed Protection

```bash
cd analog/ece_1px
./gen_tests 1px
ngspice runme_1px_tt_p_0.cir
ngspice runme_1px_ss_p_0.cir
ngspice runme_1px_fs_p_0.cir
mkdir -p ../outfiles
mv outfiles/* ../outfiles
```

### Experiment 3 : Masked Protection

```bash
cd analog/digital_v2
./run.sh -v v3 -c tt -s 0 -n 256
./run.sh -v v3 -c ss -s 0 -n 256
./run.sh -v v3 -c fs -s 0 -n 256
mkdir -p ../outfiles
mv outfiles/* ../outfiles
```

### Experiment 4 : Random Protection

```bash
cd analog/digital_v2
./run.sh -v ece -c tt -s 0 -n 256
./run.sh -v ece -c ss -s 0 -n 256
./run.sh -v ece -c fs -s 0 -n 256
mkdir -p ../outfiles
mv outfiles/* ../outfiles
```

## Digital Synthesis

```bash
make synth/counters/counter_half
make synth/samplers/double_rate_sampler
make synth/ece_1px_unprot/edge_detector
make synth/ece_1px_unprot/register_array
# etc
```

Generated spice files are manually copied to relevant libraries under their `analog/{experiment_tb}` manually assembled into the setups found there.

**Calculating Area**

Area is approximated by summing the areas of standard cells in each design.

```bash
make area
```
