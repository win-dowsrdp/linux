FROM ubuntu:latest

# 1. Install Python (needed for the web server and the systemd emulator)
RUN apt-get update && apt-get install -y python3 wget sudo

# 2. INSTALL FAKE SYSTEMD
# This script intercepts 'systemctl' commands so the installer thinks systemd is working.
RUN wget https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/master/files/docker/systemctl3.py -O /usr/bin/systemctl
RUN chmod +x /usr/bin/systemctl

# 3. SETUP THE ENVIRONMENT TO HIDE DOCKER
# We create a start script that deletes docker markers before opening the port
RUN echo '#!/bin/bash\n\
rm -f /.dockerenv\n\
rm -f /run/.containerenv\n\
python3 -m http.server 10000' > /start.sh && chmod +x /start.sh

# 4. Run the script
CMD ["/start.sh"]
