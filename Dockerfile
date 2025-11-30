FROM dockur/windows

# 1. FORCE SOFTWARE MODE (Crucial for Render)
ENV KVM="N"

# 2. SELECT LIGHTWEIGHT VERSION
# Windows 10/11 requires 2GB+ RAM and will crash Render Free Tier.
# We use XP because it runs fast on low RAM.
ENV VERSION="winxp"

# 3. SET RAM LIMIT
# Render Free tier gives ~512MB. We set this to avoid OOM kills.
ENV RAM_SIZE="400M"

# 4. ACCEPT EULA (Required to start automatically)
ENV ACCEPT_EULA="Y"

# 5. EXPOSE THE WEB VIEWER PORT
EXPOSE 8006
