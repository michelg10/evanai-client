# Claude Computer Environment Docker Replication Guide

**Generated:** September 20, 2025  
**Purpose:** Complete guide for replicating the Claude computer environment in a Docker container  
**Environment Type:** Ubuntu 24.04.3 LTS (Noble Numbat) Container  

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Base Docker Image](#base-docker-image)
3. [Environment Variables](#environment-variables)
4. [Package Management Configuration](#package-management-configuration)
5. [System Packages Installation](#system-packages-installation)
6. [Python Environment Setup](#python-environment-setup)
7. [Node.js Environment Setup](#nodejs-environment-setup)
8. [Directory Structure](#directory-structure)
9. [File Permissions](#file-permissions)
10. [Special Configurations](#special-configurations)
11. [Verification Steps](#verification-steps)
12. [Complete Dockerfile](#complete-dockerfile)

---

## System Architecture

### Base System Information
```
Operating System: Ubuntu 24.04.3 LTS (Noble Numbat)
Kernel: Linux 4.4.0 x86_64
Architecture: x86_64 GNU/Linux
Total Packages: 1,213 dpkg packages
Shared Libraries: 766 libraries in ldconfig cache
```

### Core Runtime Versions
```
Python: 3.12.3
Node.js: v18.19.1
NPM: 9.2.0
GCC: 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04)
Java: OpenJDK 21.0.8 (build 21.0.8+9-Ubuntu-0ubuntu124.04.1)
```

---

## Base Docker Image

```dockerfile
FROM ubuntu:24.04

# Set non-interactive installation mode
ARG DEBIAN_FRONTEND=noninteractive

# Update base system
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        gnupg \
        lsb-release \
        software-properties-common
```

---

## Environment Variables

```dockerfile
# Core Environment Variables
ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/root \
    IS_SANDBOX=yes \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    RUST_BACKTRACE=1 \
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Path Configuration
ENV PATH="/home/claude/.npm-global/bin:/home/claude/.local/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# SSL/Certificate Configuration
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Node.js Configuration
ENV NODE_PATH=/usr/local/lib/node_modules_global

# Playwright Configuration (if using browser automation)
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

# Proxy Configuration (adjust or remove based on your needs)
ENV HTTP_PROXY=http://21.0.0.189:15001 \
    HTTPS_PROXY=http://21.0.0.189:15001 \
    http_proxy=http://21.0.0.189:15001 \
    https_proxy=http://21.0.0.189:15001 \
    NO_PROXY="localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com" \
    no_proxy="localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com"
```

---

## Package Management Configuration

### APT Sources Configuration
```dockerfile
# Configure APT sources for Ubuntu 24.04
RUN echo 'Types: deb\n\
URIs: http://archive.ubuntu.com/ubuntu/\n\
Suites: noble noble-updates noble-backports\n\
Components: main restricted universe multiverse\n\
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n\
\n\
Types: deb\n\
URIs: http://security.ubuntu.com/ubuntu/\n\
Suites: noble-security\n\
Components: main restricted universe multiverse\n\
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg' > /etc/apt/sources.list.d/ubuntu.sources
```

### NPM Configuration
```dockerfile
# Configure NPM
RUN mkdir -p /home/claude/.npm-global && \
    npm config set prefix /home/claude/.npm-global && \
    npm config set cache /home/claude/.npm && \
    echo "cache = \"/home/claude/.npm\"\nprefix = \"/home/claude/.npm-global\"" > /etc/npmrc
```

---

## System Packages Installation

### Core Development Tools
```dockerfile
RUN apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    git \
    vim \
    nano \
    htop \
    zip \
    unzip \
    tar \
    gzip \
    bzip2 \
    xz-utils \
    jq \
    tree \
    rsync \
    openssh-client
```

### Python 3.12 and Development Libraries
```dockerfile
RUN apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-setuptools \
    python3-wheel \
    libpython3-dev \
    libpython3.12-dev
```

### Node.js 18.19.1 Installation
```dockerfile
RUN apt-get install -y \
    nodejs \
    npm \
    libnode-dev \
    node-gyp
```

### Java OpenJDK 21
```dockerfile
RUN apt-get install -y \
    openjdk-21-jdk \
    openjdk-21-jre
```

### Document Processing Tools
```dockerfile
RUN apt-get install -y \
    pandoc \
    texlive-full \
    libreoffice \
    imagemagick \
    ghostscript \
    poppler-utils \
    qpdf \
    pdftk-java \
    tesseract-ocr \
    tesseract-ocr-all
```

### Media and Graphics Libraries
```dockerfile
RUN apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    libmagickwand-dev \
    libmagickcore-dev \
    libcairo2-dev \
    libpango1.0-dev \
    librsvg2-dev \
    libgif-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev
```

### System Libraries
```dockerfile
RUN apt-get install -y \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libcurl4-openssl-dev \
    libsqlite3-dev \
    libbz2-dev \
    libreadline-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    liblapack-dev \
    libblas-dev \
    libatlas-base-dev \
    gfortran
```

### Fonts
```dockerfile
RUN apt-get install -y \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto \
    fonts-freefont-ttf \
    fontconfig \
    && fc-cache -fv
```

---

## Python Environment Setup

### Python Site Configuration
```
Python Paths:
- /usr/lib/python312.zip
- /usr/lib/python3.12
- /usr/lib/python3.12/lib-dynload
- /usr/local/lib/python3.12/dist-packages
- /usr/lib/python3/dist-packages
```

### Install Python Packages
```dockerfile
# Upgrade pip first
RUN pip3 install --upgrade pip setuptools wheel

# Core Data Science Stack
RUN pip3 install \
    numpy==2.3.3 \
    pandas==2.3.2 \
    scipy==1.14.1 \
    scikit-learn==1.7.2 \
    matplotlib==3.10.6 \
    seaborn==0.13.2 \
    plotly==5.25.0 \
    statsmodels==0.14.3

# Document Processing
RUN pip3 install \
    pypdf==5.9.0 \
    PyPDF2==3.1.1 \
    pdfplumber==0.11.4 \
    python-pptx==1.0.2 \
    openpyxl==3.1.5 \
    xlsxwriter==3.3.0 \
    python-docx==1.1.2 \
    reportlab==4.4.3 \
    camelot-py==1.0.9 \
    pytesseract==0.3.13 \
    pdf2image==1.17.0 \
    markitdown==0.1.7

# Image Processing
RUN pip3 install \
    Pillow==11.3.0 \
    scikit-image==0.25.2 \
    opencv-python==4.10.0.84 \
    imageio==2.37.0

# Web and API
RUN pip3 install \
    requests==2.32.5 \
    beautifulsoup4==4.13.5 \
    lxml==5.3.0 \
    html5lib==1.1 \
    flask==3.1.2 \
    fastapi==0.117.1 \
    uvicorn==0.34.1 \
    httpx==0.27.2 \
    aiohttp==3.11.11

# Development Tools
RUN pip3 install \
    ipython==8.31.0 \
    jupyter==1.1.1 \
    black==25.1.0 \
    pylint==3.3.3 \
    pytest==8.3.5 \
    tqdm==4.67.1

# Additional Utilities
RUN pip3 install \
    pyyaml==6.0.2 \
    python-dateutil==2.9.0 \
    click==8.2.1 \
    rich==13.10.0 \
    tabulate==0.9.0
```

---

## Node.js Environment Setup

### NPM Global Packages Installation
```dockerfile
# Document Creation Tools
RUN npm install -g \
    docx@9.5.1 \
    pptxgenjs@4.0.1 \
    pdf-lib@1.17.1 \
    sharp@0.34.3

# Web Development
RUN npm install -g \
    react@19.1.1 \
    react-dom@19.1.1 \
    react-icons@5.5.0 \
    playwright@1.55.0

# Markdown Tools
RUN npm install -g \
    marked@16.3.0 \
    markdown-pdf@11.0.0 \
    markdown-toc@1.2.0 \
    markdownlint-cli@0.45.0 \
    markdownlint-cli2@0.18.1 \
    remark-cli@12.0.1 \
    remark-preset-lint-recommended@7.0.1

# TypeScript and Development
RUN npm install -g \
    typescript@5.7.3 \
    ts-node@10.9.2 \
    tsx@4.20.5

# Diagram Tools
RUN npm install -g \
    @mermaid-js/mermaid-cli@11.10.1

# Additional Tools
RUN npm install -g \
    pdfjs-dist@5.4.149
```

---

## Directory Structure

```dockerfile
# Create essential directories
RUN mkdir -p \
    /home/claude/.npm-global/bin \
    /home/claude/.npm-global/lib \
    /home/claude/.npm \
    /home/claude/.cache \
    /home/claude/.config \
    /home/claude/.local/bin \
    /home/claude/.local/lib \
    /mnt/user-data/uploads \
    /mnt/user-data/outputs \
    /mnt/skills/public/docx \
    /mnt/skills/public/pdf \
    /mnt/skills/public/pptx \
    /mnt/skills/public/xlsx \
    /mnt/knowledge \
    /opt/pw-browsers \
    /tmp

# Set working directory
WORKDIR /home/claude
```

---

## File Permissions

```dockerfile
# Set appropriate permissions
RUN chmod -R 755 /home/claude && \
    chmod -R 755 /mnt/user-data && \
    chmod -R 755 /mnt/skills && \
    chmod -R 755 /mnt/knowledge && \
    chmod 1777 /tmp
```

---

## Special Configurations

### ImageMagick Policy Configuration
```dockerfile
# Allow PDF processing in ImageMagick
RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' \
    /etc/ImageMagick-6/policy.xml || true
```

### LibreOffice Headless Configuration
```dockerfile
# Configure LibreOffice for headless operation
RUN echo "alias soffice='soffice --headless --invisible --nodefault --nolockcheck'" >> /root/.bashrc
```

### Git Configuration
```dockerfile
# Configure Git
RUN git config --global user.name "Claude" && \
    git config --global user.email "claude@anthropic.com" && \
    git config --global init.defaultBranch main
```

### Playwright Browser Installation (Optional)
```dockerfile
# Install Playwright browsers if needed
RUN npx playwright install --with-deps chromium firefox webkit || true
```

---

## Verification Steps

### Create Verification Script
```dockerfile
# Create verification script
RUN cat > /verify_environment.sh << 'EOF'
#!/bin/bash
echo "=== Environment Verification ==="
echo "Python: $(python3 --version)"
echo "Node: $(node --version)"
echo "NPM: $(npm --version)"
echo "Java: $(java --version 2>&1 | head -1)"
echo "Pandoc: $(pandoc --version | head -1)"
echo "LibreOffice: $(soffice --version 2>&1 | head -1)"
echo "ImageMagick: $(convert --version | head -1)"
echo "LaTeX: $(pdflatex --version | head -1)"
echo "Python packages: $(pip list | wc -l)"
echo "NPM global packages: $(npm list -g --depth=0 2>/dev/null | grep '^+--' | wc -l)"
echo "System packages: $(dpkg -l | grep '^ii' | wc -l)"
echo "================================"
EOF

RUN chmod +x /verify_environment.sh
```

---

## Complete Dockerfile

```dockerfile
# Claude Computer Environment Replication
# Ubuntu 24.04.3 LTS with Python 3.12.3, Node.js 18.19.1

FROM ubuntu:24.04

# Metadata
LABEL maintainer="Claude Environment Replicator" \
      version="1.0" \
      description="Complete replication of Claude's computer environment"

# Set non-interactive mode
ARG DEBIAN_FRONTEND=noninteractive

# Environment Variables
ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/root \
    IS_SANDBOX=yes \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    RUST_BACKTRACE=1 \
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
    PATH="/home/claude/.npm-global/bin:/home/claude/.local/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    NODE_PATH=/usr/local/lib/node_modules_global \
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

# Update and install base packages
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg lsb-release software-properties-common

# Install all system packages in one layer to reduce image size
RUN apt-get update && apt-get install -y \
    # Development tools
    build-essential gcc g++ make cmake git vim nano htop \
    zip unzip tar gzip bzip2 xz-utils jq tree rsync openssh-client \
    # Python
    python3 python3-pip python3-dev python3-venv python3-setuptools \
    python3-wheel libpython3-dev libpython3.12-dev \
    # Node.js
    nodejs npm libnode-dev node-gyp \
    # Java
    openjdk-21-jdk openjdk-21-jre \
    # Document processing
    pandoc texlive-full libreoffice imagemagick ghostscript \
    poppler-utils qpdf pdftk-java tesseract-ocr tesseract-ocr-all \
    # Media libraries
    ffmpeg libavcodec-extra libmagickwand-dev libmagickcore-dev \
    libcairo2-dev libpango1.0-dev librsvg2-dev libgif-dev \
    libjpeg-dev libpng-dev libtiff-dev libwebp-dev \
    # System libraries
    libssl-dev libffi-dev libxml2-dev libxslt1-dev libcurl4-openssl-dev \
    libsqlite3-dev libbz2-dev libreadline-dev libncurses5-dev \
    libgdbm-dev libnss3-dev liblapack-dev libblas-dev \
    libatlas-base-dev gfortran \
    # Fonts
    fonts-dejavu fonts-liberation fonts-noto fonts-freefont-ttf fontconfig \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure NPM
RUN mkdir -p /home/claude/.npm-global && \
    npm config set prefix /home/claude/.npm-global && \
    npm config set cache /home/claude/.npm && \
    echo "cache = \"/home/claude/.npm\"\nprefix = \"/home/claude/.npm-global\"" > /etc/npmrc

# Install Python packages
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install \
    numpy==2.3.3 pandas==2.3.2 scipy==1.14.1 scikit-learn==1.7.2 \
    matplotlib==3.10.6 seaborn==0.13.2 plotly==5.25.0 statsmodels==0.14.3 \
    pypdf==5.9.0 PyPDF2==3.1.1 pdfplumber==0.11.4 python-pptx==1.0.2 \
    openpyxl==3.1.5 xlsxwriter==3.3.0 python-docx==1.1.2 reportlab==4.4.3 \
    camelot-py==1.0.9 pytesseract==0.3.13 pdf2image==1.17.0 markitdown==0.1.7 \
    Pillow==11.3.0 scikit-image==0.25.2 opencv-python==4.10.0.84 imageio==2.37.0 \
    requests==2.32.5 beautifulsoup4==4.13.5 lxml==5.3.0 html5lib==1.1 \
    flask==3.1.2 fastapi==0.117.1 uvicorn==0.34.1 httpx==0.27.2 aiohttp==3.11.11 \
    ipython==8.31.0 jupyter==1.1.1 black==25.1.0 pylint==3.3.3 pytest==8.3.5 \
    tqdm==4.67.1 pyyaml==6.0.2 python-dateutil==2.9.0 click==8.2.1 \
    rich==13.10.0 tabulate==0.9.0

# Install NPM global packages
RUN npm install -g \
    docx@9.5.1 pptxgenjs@4.0.1 pdf-lib@1.17.1 sharp@0.34.3 \
    react@19.1.1 react-dom@19.1.1 react-icons@5.5.0 playwright@1.55.0 \
    marked@16.3.0 markdown-pdf@11.0.0 markdown-toc@1.2.0 \
    markdownlint-cli@0.45.0 markdownlint-cli2@0.18.1 \
    remark-cli@12.0.1 remark-preset-lint-recommended@7.0.1 \
    typescript@5.7.3 ts-node@10.9.2 tsx@4.20.5 \
    @mermaid-js/mermaid-cli@11.10.1 pdfjs-dist@5.4.149

# Create directory structure
RUN mkdir -p \
    /home/claude/.npm-global/bin \
    /home/claude/.npm-global/lib \
    /home/claude/.npm \
    /home/claude/.cache \
    /home/claude/.config \
    /home/claude/.local/bin \
    /home/claude/.local/lib \
    /mnt/user-data/uploads \
    /mnt/user-data/outputs \
    /mnt/skills/public/docx \
    /mnt/skills/public/pdf \
    /mnt/skills/public/pptx \
    /mnt/skills/public/xlsx \
    /mnt/knowledge \
    /opt/pw-browsers \
    /tmp

# Set permissions
RUN chmod -R 755 /home/claude && \
    chmod -R 755 /mnt/user-data && \
    chmod -R 755 /mnt/skills && \
    chmod -R 755 /mnt/knowledge && \
    chmod 1777 /tmp

# Configure ImageMagick for PDF processing
RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' \
    /etc/ImageMagick-6/policy.xml || true

# Configure Git
RUN git config --global user.name "Claude" && \
    git config --global user.email "claude@anthropic.com" && \
    git config --global init.defaultBranch main

# Create verification script
RUN cat > /verify_environment.sh << 'EOF'
#!/bin/bash
echo "=== Claude Environment Verification ==="
echo "Python: $(python3 --version)"
echo "Node: $(node --version)"
echo "NPM: $(npm --version)"
echo "Java: $(java --version 2>&1 | head -1)"
echo "Pandoc: $(pandoc --version | head -1)"
echo "LibreOffice: $(soffice --version 2>&1 | head -1)"
echo "ImageMagick: $(convert --version | head -1)"
echo "LaTeX: $(pdflatex --version | head -1)"
echo "Python packages: $(pip list | wc -l)"
echo "NPM global packages: $(npm list -g --depth=0 2>/dev/null | grep '^+--' | wc -l)"
echo "System packages: $(dpkg -l | grep '^ii' | wc -l)"
echo "========================================"
EOF
RUN chmod +x /verify_environment.sh

# Set working directory
WORKDIR /home/claude

# Default command
CMD ["/bin/bash"]
```

---

## Building and Running the Container

### Build the Docker Image
```bash
docker build -t claude-environment:latest .
```

### Run the Container
```bash
# Basic run
docker run -it --rm claude-environment:latest

# With volume mounts for persistent data
docker run -it --rm \
  -v $(pwd)/skills:/mnt/skills \
  -v $(pwd)/knowledge:/mnt/knowledge \
  -v $(pwd)/user-data:/mnt/user-data \
  claude-environment:latest

# With resource limits (similar to Claude's environment)
docker run -it --rm \
  --memory="8g" \
  --cpus="4" \
  -v $(pwd)/skills:/mnt/skills \
  -v $(pwd)/knowledge:/mnt/knowledge \
  -v $(pwd)/user-data:/mnt/user-data \
  claude-environment:latest
```

### Verify the Environment
```bash
docker run --rm claude-environment:latest /verify_environment.sh
```

---

## Adding Skills Files

After building the container, you need to add the skills files. These should be mounted or copied into:
- `/mnt/skills/public/docx/`
- `/mnt/skills/public/pdf/`
- `/mnt/skills/public/pptx/`
- `/mnt/skills/public/xlsx/`

You can either:
1. Mount them as volumes when running the container
2. Copy them into the image during build
3. Create a derived image that adds them

Example of adding skills during build:
```dockerfile
# Add this to the Dockerfile before the final WORKDIR
COPY skills/ /mnt/skills/
```

---

## Notes and Considerations

### Security Considerations
- Remove proxy environment variables if not needed
- Consider running as non-root user in production
- Limit container capabilities as needed
- Review and adjust ImageMagick policy based on security requirements

### Optimization Opportunities
1. **Multi-stage build**: Separate build dependencies from runtime
2. **Layer caching**: Order commands to maximize cache reuse
3. **Size reduction**: Use `--no-install-recommends` more aggressively
4. **Alpine variant**: Consider Alpine Linux for smaller image size

### Differences from Original Environment
- No proxy configuration by default (can be added if needed)
- Running as root (original might have different user setup)
- No Playwright browsers installed by default (uncomment if needed)
- Simplified filesystem (no systemd, init system, etc.)

### Additional Packages to Consider
Based on your specific use case, you might want to add:
- Database clients (sqlite3, postgresql-client, mysql-client)
- Additional Python ML libraries (tensorflow, torch, transformers)
- Cloud CLIs (awscli, gcloud, azure-cli)
- Container tools (docker, kubectl)
- Additional fonts for specific language support

---

## Maintenance and Updates

### Updating Package Versions
```bash
# Update Python packages
docker run --rm claude-environment:latest pip list --outdated

# Update NPM packages
docker run --rm claude-environment:latest npm outdated -g

# Update system packages
docker run --rm claude-environment:latest apt list --upgradable
```

### Creating a Derived Image
```dockerfile
FROM claude-environment:latest

# Add your customizations
COPY my-scripts/ /home/claude/scripts/
RUN pip install my-additional-packages

# Add your skills
COPY my-skills/ /mnt/skills/
```

---

## Troubleshooting

### Common Issues and Solutions

1. **ImageMagick PDF Processing**
   - If PDFs aren't processing, check `/etc/ImageMagick-6/policy.xml`
   - Ensure PDF rights are set to "read|write"

2. **Node Module Resolution**
   - Check NODE_PATH is set correctly
   - Verify npm prefix with `npm config get prefix`

3. **Python Import Errors**
   - Verify PYTHONPATH if needed
   - Check site-packages location with `python3 -m site`

4. **LibreOffice Headless Issues**
   - Ensure running with `--headless --invisible` flags
   - Check for X11 dependencies if GUI-related errors occur

5. **Permission Denied Errors**
   - Check directory ownership and permissions
   - Consider running specific commands with appropriate user context

---

## Conclusion

This guide provides a complete blueprint for replicating the Claude computer environment in Docker. The resulting container will have:

- Full Python data science and document processing stack
- Complete Node.js/JavaScript development environment
- Comprehensive document conversion and processing tools
- Professional typesetting with LaTeX
- OCR and image processing capabilities
- Web scraping and automation tools

Combined with the provided skills files and environment inventory, this should give you a fully functional replica of the Claude computer environment suitable for:
- Document automation and processing
- Data analysis and visualization
- Web development and API creation
- General-purpose scripting and automation
- Professional document creation and manipulation

For questions or issues, refer to the verification script output and compare with the original environment inventory provided separately.
