# Dockerfile

# 1. Use an official Python runtime as a parent image
FROM python:3.9-slim

# 2. Set the working directory in the container
WORKDIR /code

# 3. Copy the requirements file into the container
COPY ./requirements.txt /code/requirements.txt

# 4. Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copy the application code into the container
COPY ./app /code/app

# 6. Expose the port the app runs on
EXPOSE 8000

# 7. Define the command to run the application
#    Uvicorn is a lightning-fast ASGI server, recommended for FastAPI.
#    --host 0.0.0.0 makes the server accessible from outside the container.
#    --port 8000 is the port to listen on.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
