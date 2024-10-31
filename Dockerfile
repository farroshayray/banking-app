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