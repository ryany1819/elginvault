# ElginVault Stock Downloader

## Introduction

ElginVault git designed to automate the process of downloading stock data, processing it into CSV files, and importing it into a stock vault system. It leverages `yfinance` for fetching stock data and provides a streamlined workflow for managing stock-related tasks.

Key features:

-   Download historical stock data for specified date ranges.
-   Process and merge data into CSV files.
-   Import data into a stock vault system with progress tracking.

---

## Setup

### Prerequisites

1. **Python**: Ensure Python 3.8 or higher is installed on your system.
2. **Poetry**: Install Poetry for dependency management:
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```
## Build and Deployment
### Building Docker Images
To build the Docker images for the API and database, run the following command:

This will build the following Docker images:

- elginvault-api: The FastAPI application.
- elginvault-db: The PostgreSQL database container.
### Deploying the Application
To deploy the application, use the deploy.sh script:

### eployment Options:
-d, --dir <path>: Specify the root directory for deployment (default: ~/docker).
-p, --port <port>: Specify the port to expose for the API (default: 8000).
-h, --help: Show the help message.
### Example Deployment:
This will:

Deploy the compose.yaml and .env files to the specified directory.
Use port 8080 for the API instance.
### Post-Deployment Instructions
1. Modify the .env file in the deployment directory to customize database and API settings.
2. Start the containers using Docker Compose:
```
docker compose up -d
```
3. The API will be accessible at http://<host>:<port> (default: http://localhost:8000).
Shell Scripts
Below is a list of available shell scripts and their purposes:

## 
| Script                    | Purpose
| ./build_all.sh	        | Builds the elginvault-api and elginvault-db Docker images.
| ./deploy.sh               | Deploys the application by generating compose.yaml and .env files.
| poetry run python vum.py	| Runs the main stock downloader script.
| rm -r <folder>	Deletes a folder and its contents (used for cleaning up temporary files).
| poetry install            | Installs all dependencies specified in pyproject.toml.
| poetry run pytest	        | Runs the test suite to validate the functionality of the project.

## Usage
1. Edit the stocks list in vum.py to specify the stocks and date ranges you want to process.
2. Run the main script:
```
poetry run python vum.py
```
3. Monitor the progress and output in the terminal.
## Contributing
Contributions are welcome! Feel free to submit issues or pull requests to improve the project.

### License
This project is licensed under the MIT License. See the LICENSE file for details.