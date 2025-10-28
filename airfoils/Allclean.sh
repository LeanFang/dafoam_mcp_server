#!/bin/bash

echo "Cleaning..."
rm -rf 0
rm -rf postProcessing
rm -rf constant/polyMesh/
rm -rf *.bin *.info *.dat *.xyz *.stl *.jpeg *.png reports *.txt *.hst
rm -rf processor* 0.00* FFD/*
rm -rf {1..9}*

