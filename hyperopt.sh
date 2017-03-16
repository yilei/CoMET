#!/usr/bin/env bash

CUDA_VISIBLE_DEVICES=0 python CoMET.py mycoplasma 500 30 -e 200 --conv 1 --fc 1 --rate .005  > logs/log0.txt &
CUDA_VISIBLE_DEVICES=1 python CoMET.py mycoplasma 200 15 --mode family -e 200 --conv 2 --fc 1 --rate .005 > logs/log1.txt &
CUDA_VISIBLE_DEVICES=2 python CoMET.py mycoplasma 200 5 --mode family -e 200 --conv 3 --fc 1 --rate .005  > logs/log2.txt &
CUDA_VISIBLE_DEVICES=3 python CoMET.py mycoplasma 200 3 --mode family -e 200 --conv 4 --fc 1 --rate .005 > logs/log3.txt &
#THEANO_FLAGS="device=gpu4" python CoMET.py dnabind 100 100 -e 200 --conv 1 --rate .01 > logs/log4.txt &
#THEANO_FLAGS="device=gpu5" python CoMET.py hsapiens 256 5 --mode family -e 200 --conv 1 --rate .01 > logs/log5.txt &
#THEANO_FLAGS="device=gpu6" python CoMET.py dnabind 100 20 --mode family -e 200 --conv 3 --rate .01 > logs/log6.txt &
#THEANO_FLAGS="device=gpu7" python CoMET.py dinbind 100 20 --mode family -e 200 --conv 3 --rate .01 > logs/log7.txt &
