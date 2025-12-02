#!/bin/bash

surfaceGenerateBoundingBox wing.stl domain.stl 20 20 20 20 0 20
cartesianMesh
renumberMesh -overwrite
checkMesh

