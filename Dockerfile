FROM dafoam/opt-packages:latest
USER dafoamuser
WORKDIR /home/dafoamuser/dafoam
COPY dafoam_mcp_server.py .
CMD ["/home/dafoamuser/dafoam/packages/miniconda3/bin/python", "-u", "dafoam_mcp_server.py"]