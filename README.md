Postman documentation link: [Postman documentation](https://documenter.getpostman.com/view/37782623/2sAY4vhiD5)  
Flask Deployed project: [Deployed App](https://enthusiastic-beaver-farroshayray-fa549bb9.koyeb.app/)


# Documentation for Flask Banking Application

This document provides a step-by-step guide for:

1. [Create and Run a Flask Application with Poetry](#1-create-and-run-a-flask-application-with-poetry)
2. [Install Dependencies from `pyproject.toml`](#2-install-dependencies-from-pyprojecttoml)
3. [Creating a Dockerfile for Containerization](#3-creating-a-dockerfile-for-containerization)
4. [Deploying the Application on Koyeb](#4-deploying-the-application-on-koyeb)

---

## 1. Create and Run a Flask Application with Poetry

### Step 1: Install Poetry
Install Poetry if you haven’t done so already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
Or refer to the [Poetry installation guide](https://python-poetry.org/docs/#installation) for other methods.

### Step 2: Create a New Flask Project
Initialize a new project using Poetry:
```bash
poetry new farros-banking
```
Navigate into the project folder:
```bash
cd farros-banking
```

### Step 3: Configure the Flask Application
Update `pyproject.toml` with the following settings to set up your Flask app:
```toml
[tool.poetry]
name = "farros-banking"
version = "0.1.0"
description = ""
authors = ["farroshayray <farros.hr@gmail.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.12"
flask = "^3.0.3"
mysql-connector-python = "^9.1.0"
python-dotenv = "^1.0.1"
werkzeug = "^3.0.6"
pymysql = "^1.1.1"
flask-sqlalchemy = "^3.1.1"
flask-jwt-extended = "^4.6.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Step 4: Create the Flask App
Create a new file `app.py` in the project root with the following code:
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Farros Banking Application!"

if __name__ == '__main__':
    app.run(debug=True)
```

### Step 5: Run the Application
Activate the Poetry environment and run the app:
```bash
poetry install
poetry run python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000` to see the Flask app in action.

---

## 2. Install Dependencies from `pyproject.toml`

To install dependencies as specified in `pyproject.toml`, run:
```bash
poetry install
```

This will install all the required packages:
- `flask`
- `mysql-connector-python`
- `python-dotenv`
- `werkzeug`
- `pymysql`
- `flask-sqlalchemy`
- `flask-jwt-extended`

---

## 3. Creating a Dockerfile for Containerization

Create a `Dockerfile` in the root directory of your project with the following content:

```dockerfile
# Stage 1: Base image with Python 3.12 and Poetry installation
FROM python:3.12-slim-bookworm AS base

# Install Poetry
RUN pip install poetry

# Set environment variables for Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Add Poetry to the system PATH
ENV PATH="$PATH:$POETRY_HOME/bin"

# Stage 2: Build stage
FROM base AS build

# Set the working directory inside the container
WORKDIR /app

# Copy the pyproject.toml file to the container
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry install --only=main

# Copy the rest of the application code
COPY . .

# Stage 3: Runtime stage
FROM base AS runtime

# Set the working directory inside the container
WORKDIR /app

# Copy all built files from the build stage to runtime stage
COPY --from=build /app /app

# Copy the .env file into the container
# COPY .env .env

# Activate the virtual environment created by Poetry
ENV PATH="/app/.venv/bin:$PATH"
RUN echo "source /app/.venv/bin/activate" >> /etc/profile.d/venv.sh

# Expose the port 5000 for Flask
EXPOSE 5000

# Set the default command to run the Flask app
CMD ["flask", "run", "--host", "0.0.0.0"]
```

### Build and Run the Docker Image Locally
To test the container locally, build and run the Docker image:
```bash
docker build -t farros-banking .
docker run -p 5000:5000 farros-banking
```

Navigate to `http://127.0.0.1:5000` to verify the application is running correctly in the container.

---

## 4. Deploying the Application on Koyeb

### Step 1: Set Up a Koyeb Account
- Sign up or log in to [Koyeb](https://www.koyeb.com/).
- Create a new application from the dashboard.

### Step 2: Link Your Repository
- Connect your GitHub, GitLab, or Bitbucket repository to Koyeb.
- Select the repository containing your Flask app.

### Step 3: Configure Deployment Settings
- In the deployment configuration, specify the following Docker settings:
  - **Build Command**: Leave empty, as Koyeb will handle the Dockerfile automatically.
  - **Expose Port**: Ensure `5000` is specified as the app runs on this port.

### Step 4: Set Environment Variables (Optional)
If you have environment variables (like database credentials), set them in the Koyeb environment variable settings.

### Step 5: Deploy the Application
- Click "Deploy" to start the deployment process.
- Once deployed, Koyeb will provide a URL to access your application.

You can now access your application at the generated Koyeb URL. Your Flask application is successfully containerized and deployed on Koyeb.

---
