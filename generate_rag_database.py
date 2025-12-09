# generate_rag_database.py - Enhanced with metadata and structure
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pathlib import Path
import os

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 1. Load DAFoam docs (existing)
loader = DirectoryLoader("./DAFoam.github.io/pages/mydoc/", glob="**/*.md", loader_cls=TextLoader)
documents = loader.load()


# 2. Load tutorials with metadata, i.e., the folder structure as context
def load_tutorials_with_metadata(tutorials_root="./tutorials"):
    """Load tutorial files with case context"""
    from langchain.schema import Document

    tutorial_docs = []

    for case_dir in Path(tutorials_root).iterdir():
        if not case_dir.is_dir() or case_dir.name.startswith("."):
            continue

        case_name = case_dir.name

        # Create structure summary document
        tree_lines = [f"Tutorial Case: {case_name}\n\nFolder Structure:"]

        for root, dirs, files in os.walk(case_dir):
            level = root.replace(str(case_dir), "").count(os.sep)
            indent = "  " * level
            tree_lines.append(f"{indent}{os.path.basename(root)}/")

            sub_indent = "  " * (level + 1)
            for file in files:
                tree_lines.append(f"{sub_indent}{file}")

        structure_doc = Document(
            page_content="\n".join(tree_lines) + "\n",
            metadata={"case_name": case_name, "type": "structure", "source": str(case_dir)},
        )
        tutorial_docs.append(structure_doc)

    return tutorial_docs


# Load both sources
tutorial_docs = load_tutorials_with_metadata()
all_documents = documents + tutorial_docs

# Split only docs content (not structure/config bundles)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)

chunks = []
for doc in all_documents:
    if doc.metadata.get("type") == "structure":
        chunks.append(doc)  # Keep as-is
    else:
        chunks.extend(text_splitter.split_documents([doc]))

# Create vector database
vectorstore = Chroma.from_documents(documents=chunks, embedding=embedding, persist_directory="./dafoam_chroma_db")

print(f"Indexed {len(chunks)} chunks from {len(documents)} docs + {len(tutorial_docs)} tutorial items")
