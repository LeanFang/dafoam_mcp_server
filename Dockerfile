FROM dafoam/opt-packages:mcp
USER dafoamuser
WORKDIR /home/dafoamuser/mount

# This is critical - tells Docker what to run when container starts
CMD ["/home/dafoamuser/dafoam/packages/miniconda3/bin/python", "-u", "dafoam_mcp_server.py"]
