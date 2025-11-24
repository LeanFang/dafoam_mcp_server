FROM dafoam/opt-packages:mcp
USER dafoamuser
RUN /home/dafoamuser/dafoam/packages/miniconda3/bin/pip install --no-cache-dir fastmcp
WORKDIR /home/dafoamuser/mount
COPY dafoam_mcp_server.py .
EXPOSE 8001
CMD ["/home/dafoamuser/dafoam/packages/miniconda3/bin/python", "-u", "dafoam_mcp_server.py"]
