#!/bin/bash

python trace_cacher.py -D nlg_xx_tt:max dig_xx_tt:max -o ../../analog/outfiles/cmb_xx_tt
python trace_cacher.py -D nlg_xx_ss:max dig_xx_ss:max -o ../../analog/outfiles/cmb_xx_ss
python trace_cacher.py -D nlg_xx_fs:max dig_xx_fs:max -o ../../analog/outfiles/cmb_xx_fs
python trace_cacher.py -D nlg_xp_tt:max dig_xp_tt:max -o ../../analog/outfiles/cmb_xp_tt
python trace_cacher.py -D nlg_xp_ss:max dig_xp_ss:max -o ../../analog/outfiles/cmb_xp_ss
python trace_cacher.py -D nlg_xp_fs:max dig_xp_fs:max -o ../../analog/outfiles/cmb_xp_fs
