#Honestly, not sure where this should go, but from what it seems we need Ubuntu 24, python 3.12 cuz using pyth0n 3.13 from ubuntu
#causes some weird problems
FROM ubuntu:24.04
FROM python:3.12

# Avoid interactive prompts during package installs 
ENV DEBIAN_FRONTEND=noninteractive 
# Update and install basic tools, python tools and npm tools
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y \
    nodejs \
    # Python system packages
    python3-apt \
    python3-dbus \
    python3-gi \
    python3-cairo \
    python3-cairo-dev \
    libgirepository1.0-dev \
    libdbus-1-dev \
    libcairo2-dev \
    # More system tools
    pandoc \
    ffmpeg \
    tesseract-ocr \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    # For sharp (image processing)
    libvips-dev \
    # For playwright (browser automation)
    libnss3-dev \
    libatk-bridge2.0-dev \
    libdrm2 \
    libxkbcommon-dev \
    libxcomposite-dev \
    libxdamage-dev \
    libxrandr2 \
    libgbm-dev \
    libxss1 \
    libasound2-dev \
    # For PDF processing and fonts
    fonts-liberation \
    libappindicator3-1 \
    # For mermaid-cli (puppeteer dependencies)
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*
# Update and install tools here 


#PYTHON
# Download the latest uv installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"
# Make venv
RUN uv venv
# Install packages 
COPY requirements.txt . 
RUN uv pip install -r requirements.txt

#NPM and NODE

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs
# Set npm global directory and PATH
ENV NPM_CONFIG_PREFIX=/home/claude/.npm-global
ENV PATH=$PATH:/home/claude/.npm-global/bin

# Create npm global directory
RUN mkdir -p /home/claude/.npm-global

# Install npm packages that provide your binary tools
RUN npm install -g \
    @mermaid-js/mermaid-cli \
    markdown-pdf \
    markdown-toc \
    markdownlint-cli \
    markdownlint-cli2 \
    marked \
    playwright \
    remark-cli \
    ts-node \
    typescript \
    tsx
# Install playwright browsers for browser automation
RUN npx playwright install --with-deps




#CHANGES TO REQUIREMENTS.TXT
#removing this because it has to be downloaded through ubuntu
#python-apt==2.7.7+ubuntu5
#dbus-python==1.3.2
#PyGObject==3.48.2
#pycairo==1.28.0
#rlPyCairo==0.4.0
#removing this because it seems like it was deprecated
#gyp==0.1
