FROM dockur/windows

# 1. SELECT WINDOWS 10
ENV VERSION="win10"

# 2. DISABLE KVM (Mandatory on Render)
# Even on Pro tier, Render does not expose hardware virtualization.
# We set this to "N" to force Software Emulation (TCG) so it starts without crashing.
ENV KVM="N"

# 3. ALLOCATE PRO RESOURCES
# Since you are on Pro/Max, we give it plenty of juice.
# Adjust 'RAM_SIZE' based on your specific plan (e.g., if you have 8GB plan, give it 7G).
ENV RAM_SIZE="8G"
ENV CPU_CORES="4"

# 4. DISK SPACE
# Windows 10 needs space. Ensure your Render plan has enough ephemeral storage.
ENV DISK_SIZE="64G"

# 5. AUTOMATION
# Accept EULA automatically so it boots straight to desktop.
ENV ACCEPT_EULA="Y"

# 6. EXPOSE WEB VIEWER
EXPOSE 8006
