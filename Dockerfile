FROM dafoam/opt-packages:latest

USER root
RUN apt-get update && apt-get install -y libxft2 && rm -rf /var/lib/apt/lists/* && apt-get clean

USER dafoamuser
WORKDIR /home/dafoamuser/dafoam/packages

RUN /home/dafoamuser/dafoam/packages/miniconda3/bin/pip install fastmcp==2.13.2 vtk==9.5.2 trame==3.12.0 trame-vuetify==3.2.0 trame-vtk==2.10.0 gmsh==4.15.0 && \
    wget https://www.paraview.org/files/v5.13/ParaView-5.13.3-egl-MPI-Linux-Python3.10-x86_64.tar.gz && \
    tar -xf ParaView-5.13.3-egl-MPI-Linux-Python3.10-x86_64.tar.gz && \
    mv ParaView-5.13.3-egl-MPI-Linux-Python3.10-x86_64 ParaView-5.13.3 && \
    rm -rf ParaView-5.13.3-egl-MPI-Linux-Python3.10-x86_64.tar.gz && \
    mv ParaView-5.13.3/bin/mpiexec  ParaView-5.13.3/bin/mpiexec_bk && \
    echo "# ParaView" >> /home/dafoamuser/dafoam/loadDAFoam.sh && \
    echo "export PATH=\$DAFOAM_ROOT_PATH/packages/ParaView-5.13.3/bin:\$PATH" >> /home/dafoamuser/dafoam/loadDAFoam.sh

WORKDIR /home/dafoamuser/mount

# This is critical - tells Docker what to run when container starts
# Use bash to source the environment before running the MCP server
CMD ["bash", "-c", "source /home/dafoamuser/dafoam/loadDAFoam.sh && python -u dafoam_mcp_server.py"]
