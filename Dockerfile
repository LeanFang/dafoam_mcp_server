FROM dafoam/opt-packages:mcp
USER dafoamuser
WORKDIR /home/dafoamuser

# Install langchain and chromadb with compatible versions
# sentence-transformers 2.2.2 is compatible with numpy 1.23.5 and scipy 1.15.1
RUN /home/dafoamuser/dafoam/packages/miniconda3/bin/pip install \
    langchain-community==0.3.1 \
    langchain-text-splitters==0.3.0 \
    chromadb==0.4.24 \
    sentence-transformers==3.3.1 \
    --break-system-packages

# Copy and run RAG generation
COPY generate_rag_database.py .
RUN wget https://github.com/DAFoam/DAFoam.github.io/archive/refs/heads/main.tar.gz && \
    tar -xvf main.tar.gz && mv DAFoam.github.io-main DAFoam.github.io && \
    wget -O tutorials-main.tar.gz https://github.com/DAFoam/tutorials/archive/refs/heads/main.tar.gz && \
    tar -xvf tutorials-main.tar.gz && mv tutorials-main tutorials && \
    /home/dafoamuser/dafoam/packages/miniconda3/bin/python generate_rag_database.py && \
    rm -rf DAFoam.github.io main.tar.gz generate_rag_database.py tutorials-main.tar.gz tutorials

# Set working directory for runtime (where dafoam_mcp_server.py will be mounted)
WORKDIR /home/dafoamuser/mount

# This is critical - tells Docker what to run when container starts
CMD ["/home/dafoamuser/dafoam/packages/miniconda3/bin/python", "-u", "dafoam_mcp_server.py"]
