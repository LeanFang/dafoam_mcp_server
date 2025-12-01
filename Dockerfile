FROM dafoam/opt-packages:mcp
USER dafoamuser
WORKDIR /home/dafoamuser/mount
COPY dafoam_mcp_server.py .
EXPOSE 8001
CMD ["/home/dafoamuser/dafoam/packages/miniconda3/bin/python", "-u", "dafoam_mcp_server.py"]
