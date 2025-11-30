FROM ubuntu:latest

# 1. Update and install python3 (ubuntu:latest is minimal and doesn't have it)
RUN apt-get update && apt-get install -y python3

# 2. Command to run a dummy server on port 10000
CMD ["python3", "-m", "http.server", "10000"]
