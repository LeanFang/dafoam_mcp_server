FROM dafoam/opt-packages:latest
USER dafoamuser
WORKDIR /home/dafoamuser/dafoam
COPY airfoil_mcp.py .
CMD ["/home/dafoamuser/dafoam/packages/miniconda3/bin/python", "-u", "airfoil_mcp.py"]