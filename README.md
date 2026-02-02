# Secure-Group-Chat-AAU
An implementation of a secure group chat utilizing E2EE.

### Install UV & Usage
1. Installation of [UV](https://docs.astral.sh/uv/)
```bash
# Install UV on windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install on MAC
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
wget -qO- https://astral.sh/uv/install.sh | sh
```
If nothing works visit: https://docs.astral.sh/uv/getting-started/installation/


2. Usage Examples of UV
- `uv run` Run a command in the project environment. (like python main.py)

- `uv sync` Sync the project's dependencies with the environment.
  
- `uv add` Add a dependency to the project.

- `uv self update` Update uv to the latest version.
  
- `uv remove` Remove a dependency from the project.
    
- `uv init` Create a new Python project.


## Installation & Setup
1. Clone the repository
```bash
# Clone this repository with git
git clone project_link

# Open the directory in terminal
cd Secure-Group-Chat-AAU/
```

2. Create Virtual Environment & Download packages
```bash
uv sync

# If u get an error try this!
uv sync --link-mode=copy
```

1. Run the program
```bash
# Run the Client
uv run --package client client

# Run the Server
uv run --package server server
```


# Tools for the development

**Add libaries/Dependencies**
```bash
# Add libary to the Client (do not write <>, e.g., requests)
uv add --package client <libary_here>

# Add libary to the Client (do not write <>, e.g., fastapi)
uv add --package server <libary_here>
```



# Demo Section (not important yet)

**Building Program (demo not tested yet!)**
```bash
# Build the Client
uv run pyinstaller --onefile --noconsole --name "SecureChatClient" Client/src/client/main.py

# Build the Server
uv run pyinstaller --onefile --noconsole --name "SecureChatServer" Server/src/client/main.py
```