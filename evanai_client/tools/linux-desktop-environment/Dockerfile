# Claude Computer Environment Replication
# Ubuntu 24.04.3 LTS with Python 3.12.3, Node.js 18.19.1
# Based on environment_reference documentation

FROM ubuntu:24.04

# Metadata
LABEL maintainer="EvanAI Linux Desktop Environment" \
      version="2.0" \
      description="Complete replication of Claude's computer environment for EvanAI"

# Set non-interactive mode
ARG DEBIAN_FRONTEND=noninteractive

# Environment Variables (Core)
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
ENV NODE_PATH=/usr/local/lib/node_modules_global \
    NPM_CONFIG_PREFIX=/home/claude/.npm-global

# Playwright Configuration
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

# Note: Proxy configuration removed - add if needed for your environment
# ENV HTTP_PROXY=... HTTPS_PROXY=... NO_PROXY=...

# Locale and timezone
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    TZ=UTC

# Update and install base packages
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg lsb-release software-properties-common \
    locales && \
    locale-gen en_US.UTF-8

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

# Install all system packages in one layer to reduce image size
RUN apt-get update && apt-get install -y \
    # Development tools
    build-essential gcc g++ make cmake git vim nano htop \
    zip unzip tar gzip bzip2 xz-utils jq tree rsync openssh-client \
    # Python 3.12
    python3 python3-pip python3-dev python3-venv python3-setuptools \
    python3-wheel libpython3-dev libpython3.12-dev \
    # Additional Python system packages
    python3-apt python3-dbus python3-gi python3-cairo python3-cairo-dev \
    libgirepository1.0-dev libdbus-1-dev \
    # Node.js 18.x
    nodejs npm libnode-dev node-gyp \
    # Java OpenJDK 21
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
    # Additional libraries for sharp and playwright
    libvips-dev libatk-bridge2.0-dev libdrm2 libxkbcommon-dev \
    libxcomposite-dev libxdamage-dev libxrandr2 libgbm-dev \
    libxss1 libasound2-dev libgtk-3-0 libappindicator3-1 \
    # Fonts
    fonts-dejavu fonts-liberation fonts-noto fonts-freefont-ttf fontconfig \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure NPM
RUN mkdir -p /home/claude/.npm-global /home/claude/.npm && \
    npm config set prefix /home/claude/.npm-global && \
    npm config set cache /home/claude/.npm && \
    echo 'cache = "/home/claude/.npm"' > /etc/npmrc && \
    echo 'prefix = "/home/claude/.npm-global"' >> /etc/npmrc

# Upgrade pip and install Python packages
RUN pip3 install --upgrade pip setuptools wheel

# Install Python packages - Core Data Science Stack
RUN pip3 install \
    numpy==2.3.3 \
    pandas==2.3.2 \
    scipy==1.14.1 \
    scikit-learn==1.7.2 \
    matplotlib==3.10.6 \
    seaborn==0.13.2 \
    plotly==5.25.0 \
    statsmodels==0.14.3

# Install Python packages - Document Processing
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

# Install Python packages - Image Processing
RUN pip3 install \
    Pillow==11.3.0 \
    scikit-image==0.25.2 \
    opencv-python==4.10.0.84 \
    imageio==2.37.0

# Install Python packages - Web and API
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

# Install Python packages - Development Tools
RUN pip3 install \
    ipython==8.31.0 \
    jupyter==1.1.1 \
    black==25.1.0 \
    pylint==3.3.3 \
    pytest==8.3.5 \
    tqdm==4.67.1

# Install Python packages - Additional Utilities
RUN pip3 install \
    pyyaml==6.0.2 \
    python-dateutil==2.9.0 \
    click==8.2.1 \
    rich==13.10.0 \
    tabulate==0.9.0

# Install NPM global packages - Document Creation Tools
RUN npm install -g \
    docx@9.5.1 \
    pptxgenjs@4.0.1 \
    pdf-lib@1.17.1 \
    sharp@0.34.3

# Install NPM global packages - Web Development
RUN npm install -g \
    react@19.1.1 \
    react-dom@19.1.1 \
    react-icons@5.5.0 \
    playwright@1.55.0

# Install NPM global packages - Markdown Tools
RUN npm install -g \
    marked@16.3.0 \
    markdown-pdf@11.0.0 \
    markdown-toc@1.2.0 \
    markdownlint-cli@0.45.0 \
    markdownlint-cli2@0.18.1 \
    remark-cli@12.0.1 \
    remark-preset-lint-recommended@7.0.1

# Install NPM global packages - TypeScript and Development
RUN npm install -g \
    typescript@5.7.3 \
    ts-node@10.9.2 \
    tsx@4.20.5

# Install NPM global packages - Diagram and Additional Tools
RUN npm install -g \
    @mermaid-js/mermaid-cli@11.10.1 \
    pdfjs-dist@5.4.149

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

# Copy skills directory contents if available
COPY skills/ /mnt/skills/

# Set permissions
RUN chmod -R 755 /home/claude && \
    chmod -R 755 /mnt/user-data && \
    chmod -R 755 /mnt/skills && \
    chmod -R 755 /mnt/knowledge && \
    chmod 1777 /tmp

# Configure ImageMagick for PDF processing
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
        sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' \
        /etc/ImageMagick-6/policy.xml; \
    fi

# Configure Git
RUN git config --global user.name "Claude" && \
    git config --global user.email "claude@anthropic.com" && \
    git config --global init.defaultBranch main

# Configure LibreOffice for headless operation
RUN echo "alias soffice='soffice --headless --invisible --nodefault --nolockcheck'" >> /root/.bashrc

# Install Playwright browsers (optional - uncomment if needed)
# RUN npx playwright install --with-deps chromium firefox webkit || true

# Create verification script
RUN cat > /verify_environment.sh << 'EOF'
#!/bin/bash
echo "=== Claude Environment Verification ==="
echo ""
echo "System Information:"
echo "  OS: $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  Kernel: $(uname -r)"
echo "  Architecture: $(uname -m)"
echo ""
echo "Core Tools:"
echo "  Python: $(python3 --version)"
echo "  Node: $(node --version)"
echo "  NPM: $(npm --version)"
echo "  Java: $(java --version 2>&1 | head -1)"
echo "  GCC: $(gcc --version | head -1)"
echo ""
echo "Document Processing:"
echo "  Pandoc: $(pandoc --version 2>/dev/null | head -1 || echo 'not found')"
echo "  LibreOffice: $(soffice --version 2>&1 | head -1 || echo 'not found')"
echo "  ImageMagick: $(convert --version 2>/dev/null | head -1 || echo 'not found')"
echo "  LaTeX: $(pdflatex --version 2>/dev/null | head -1 || echo 'not found')"
echo "  Tesseract: $(tesseract --version 2>&1 | head -1 || echo 'not found')"
echo ""
echo "Package Counts:"
echo "  Python packages: $(pip list 2>/dev/null | tail -n +3 | wc -l)"
echo "  NPM global packages: $(npm list -g --depth=0 2>/dev/null | grep -c '^├─\|^└─' || echo '0')"
echo "  System packages: $(dpkg -l 2>/dev/null | grep -c '^ii' || echo '0')"
echo ""
echo "Directory Structure:"
ls -la /mnt/ 2>/dev/null | head -5
echo ""
echo "Environment Variables (selected):"
env | grep -E '^(PATH|PYTHON|NODE|JAVA|HOME|NPM)' | head -10
echo ""
echo "========================================"
EOF

RUN chmod +x /verify_environment.sh

# Create a simple test script
RUN cat > /test_tools.sh << 'EOF'
#!/bin/bash
echo "=== Testing Tool Functionality ==="
echo ""

# Test Python imports
echo "Testing Python imports..."
python3 -c "import numpy, pandas, sklearn, matplotlib, flask, PIL, cv2, requests, bs4" && echo "✓ Core Python packages work" || echo "✗ Python package import failed"

# Test Node modules
echo ""
echo "Testing Node modules..."
node -e "console.log('Node.js works')" && echo "✓ Node.js works" || echo "✗ Node.js failed"
npx tsc --version >/dev/null 2>&1 && echo "✓ TypeScript available" || echo "✗ TypeScript not found"

# Test document tools
echo ""
echo "Testing document tools..."
echo "# Test" | pandoc -f markdown -t html >/dev/null 2>&1 && echo "✓ Pandoc works" || echo "✗ Pandoc failed"
convert -version >/dev/null 2>&1 && echo "✓ ImageMagick works" || echo "✗ ImageMagick failed"

echo ""
echo "========================="
EOF

RUN chmod +x /test_tools.sh

# Set working directory
WORKDIR /home/claude

# Default command
CMD ["/bin/bash"]