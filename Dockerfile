# CORRECTED IMAGE NAME: 'dockurr' with two r's
FROM dockurr/windows:latest

# 1. SELECT WINDOWS 10
ENV VERSION="win10"

# 2. DISABLE KVM (CRITICAL FOR RENDER)
# Render does not support KVM (Hardware Virtualization), even on Pro.
# We must set this to "N" to force Software Mode, or it will crash on boot.
ENV KVM="N"

# 3. MAXIMIZE RESOURCES (PRO TIER)
# Adjust these based on your specific Render plan limits.
ENV RAM_SIZE="8G"
ENV CPU_CORES="4"
ENV DISK_SIZE="64G"

# 4. SETUP AUTOMATION
ENV ACCEPT_EULA="Y"

# 5. EXPOSE WEB VIEWER
EXPOSE 8006
