# Claude Environment Technical Details Supplement

**Generated:** September 20, 2025  
**Purpose:** Additional technical specifications for exact environment replication  

---

## Detailed Package Versions Reference

### Critical System Packages (dpkg)

```bash
# Core Libraries
libgcc-s1:amd64                    14.2.0-4ubuntu2~24.04
libstdc++6:amd64                   14.2.0-4ubuntu2~24.04
libc6:amd64                        2.39-0ubuntu8.5
libssl3t64:amd64                   3.0.13-0ubuntu3.4
libcurl4t64:amd64                  8.5.0-2ubuntu10.6

# Python Related
python3.12                         3.12.3-1ubuntu0.8
python3.12-minimal                 3.12.3-1ubuntu0.8
python3.12-dev                     3.12.3-1ubuntu0.8
libpython3.12-stdlib               3.12.3-1ubuntu0.8
libpython3.12t64                   3.12.3-1ubuntu0.8
python3-pip                        24.0+dfsg-1ubuntu1.1
python3-setuptools                 68.1.2-2ubuntu1.1
python3-wheel                      0.42.0-2
python3-venv                       3.12.3-0ubuntu2

# Node.js Related
nodejs                             18.19.1+dfsg-6ubuntu5
npm                                9.2.0~ds1-3
libnode109                         18.19.1+dfsg-6ubuntu5
libnode-dev                        18.19.1+dfsg-6ubuntu5
node-gyp                           10.0.1-1

# Document Processing
pandoc                             3.1.11.1+ds-1ubuntu1
pandoc-data                        3.1.11.1+ds-1ubuntu1
texlive-full                       2023.20240207-1
libreoffice                        4:24.2.7-0ubuntu0.24.04.4
imagemagick                        8:6.9.12.98+dfsg1-5.2build2
poppler-utils                      24.02.0-1ubuntu9.6
qpdf                               11.9.0-1.1build1
tesseract-ocr                      5.3.4-1.1build1

# Development Tools
gcc-13                             13.3.0-6ubuntu2~24.04
g++-13                             13.3.0-6ubuntu2~24.04
make                               4.3-4.1build2
cmake                              3.28.3-1build7
git                                1:2.43.0-1ubuntu7.3
```

### Complete Python Package List with Exact Versions

```python
# Data Science Core
numpy==2.3.3
pandas==2.3.2
scipy==1.14.1
scikit-learn==1.7.2
scikit-image==0.25.2
statsmodels==0.14.3

# Visualization
matplotlib==3.10.6
seaborn==0.13.2
plotly==5.25.0
bokeh==3.6.2
altair==5.5.1

# Document Processing
pypdf==5.9.0
PyPDF2==3.1.1
pdfplumber==0.11.4
python-pptx==1.0.2
openpyxl==3.1.5
xlsxwriter==3.3.0
python-docx==1.1.2
reportlab==4.4.3
camelot-py==1.0.9
pytesseract==0.3.13
pdf2image==1.17.0
pypdfium==3.1.1
markitdown==0.1.7
pandoc==2.4.1

# Image Processing
Pillow==11.3.0
opencv-python==4.10.0.84
imageio==2.37.0
scikit-video==1.1.11
imutils==0.5.4

# Web Scraping & APIs
requests==2.32.5
urllib3==2.3.0
beautifulsoup4==4.13.5
lxml==5.3.0
html5lib==1.1
scrapy==2.12.0
selenium==4.27.1
httpx==0.27.2
aiohttp==3.11.11

# Web Frameworks
flask==3.1.2
flask-cors==5.0.0
fastapi==0.117.1
uvicorn==0.34.1
starlette==0.42.0
pydantic==2.10.7

# Development Tools
ipython==8.31.0
jupyter==1.1.1
notebook==7.3.2
jupyterlab==4.3.4
black==25.1.0
pylint==3.3.3
flake8==7.1.1
mypy==1.14.2
pytest==8.3.5
pytest-cov==6.0.0
tox==4.24.0

# Database
sqlalchemy==2.0.37
psycopg2-binary==2.9.10

# Utilities
click==8.2.1
rich==13.10.0
typer==0.15.1
tqdm==4.67.1
tabulate==0.9.0
colorama==0.4.6
termcolor==2.5.0
pyyaml==6.0.2
toml==0.10.2
python-dateutil==2.9.0
pytz==2025.1
pendulum==3.0.0
arrow==1.3.0
humanize==4.12.0
python-dotenv==1.0.1
configparser==7.1.0
argparse==1.4.0
fire==0.8.1

# Cryptography & Security
cryptography==46.0.0
pycryptodome==3.22.0
passlib==1.7.4
bcrypt==4.2.1

# Additional Scientific
sympy==1.13.3
networkx==3.4.2
pygraphviz==1.14
pydot==3.0.3

# NLP & Text Processing
textblob==0.18.0.post0
ftfy==6.3.2
chardet==5.2.0
```

### NPM Global Packages Full Details

```json
{
  "dependencies": {
    "@mermaid-js/mermaid-cli": "11.10.1",
    "docx": "9.5.1",
    "markdown-pdf": "11.0.0",
    "markdown-toc": "1.2.0",
    "markdownlint-cli": "0.45.0",
    "markdownlint-cli2": "0.18.1",
    "marked": "16.3.0",
    "pdf-lib": "1.17.1",
    "pdfjs-dist": "5.4.149",
    "playwright": "1.55.0",
    "pptxgenjs": "4.0.1",
    "react": "19.1.1",
    "react-dom": "19.1.1",
    "react-icons": "5.5.0",
    "remark-cli": "12.0.1",
    "remark-preset-lint-recommended": "7.0.1",
    "sharp": "0.34.3",
    "ts-node": "10.9.2",
    "tsx": "4.20.5",
    "typescript": "5.7.3"
  }
}
```

---

## System Configuration Files

### /etc/npmrc
```
cache = "/home/claude/.npm"
prefix = "/home/claude/.npm-global"
```

### /home/claude/.npmrc
```
prefix=/home/claude/.npm-global
cache=/home/claude/.npm
```

### Python Site Packages Paths
```
System site-packages:
  /usr/local/lib/python3.12/dist-packages
  /usr/lib/python3/dist-packages

User site-packages (if exists):
  /root/.local/lib/python3.12/site-packages
```

### Shared Library Dependencies (Key Libraries)

```bash
# Core System Libraries
libz.so.1                   # Compression
libssl.so.3                 # SSL/TLS
libcrypto.so.3             # Cryptography
libcurl.so.4               # URL transfer
libsqlite3.so.0            # SQLite database
libreadline.so.8           # Command line editing
libncursesw.so.6          # Terminal handling

# Image Processing
libpng16.so.16            # PNG support
libjpeg.so.8              # JPEG support
libtiff.so.6              # TIFF support
libwebp.so.7              # WebP support
libopenjp2.so.7           # JPEG 2000
libMagickCore-6.Q16.so.7  # ImageMagick core
libMagickWand-6.Q16.so.7  # ImageMagick wand

# PDF & Document
libpoppler.so.134         # PDF rendering
libcairo.so.2             # 2D graphics
libpango-1.0.so.0         # Text layout
librsvg-2.so.2            # SVG rendering

# Media Processing
libavcodec.so.60          # Audio/video codecs
libavformat.so.60         # Media formats
libavutil.so.58           # Media utilities
libswscale.so.7           # Video scaling

# Scientific Computing
libblas.so.3              # Basic Linear Algebra
liblapack.so.3            # Linear Algebra Package
libgfortran.so.5          # Fortran runtime
libatlas.so.3             # ATLAS math library

# Python Specific
libpython3.12.so.1.0      # Python runtime

# Node.js Specific
libnode.so.109            # Node.js runtime
libv8.so                  # V8 JavaScript engine
```

---

## File System Layout

### Directory Permissions and Ownership

```bash
/home/claude              drwxr-xr-x  root:root
├── .cache               drwxr-xr-x  root:root
├── .config              drwxr-xr-x  root:root
├── .local               drwxr-xr-x  root:root
├── .npm                 drwxr-xr-x  root:root
├── .npm-global          drwxr-xr-x  root:root
│   ├── bin             drwxr-xr-x  root:root
│   └── lib             drwxr-xr-x  root:root
└── .npmrc              -rw-r--r--  root:root

/mnt/user-data           drwxr-xr-x  root:root
├── uploads             drwxr-xr-x  root:root
└── outputs             drwxr-xr-x  root:root

/mnt/skills              drwxr-xr-x  root:root
└── public              drwxr-xr-x  root:root
    ├── docx           drwxr-xr-x  root:root
    ├── pdf            drwxr-xr-x  root:root
    ├── pptx           drwxr-xr-x  root:root
    └── xlsx           drwxr-xr-x  root:root

/mnt/knowledge           drwxr-xr-x  999:root
```

### Binary Locations

```bash
# System binaries (unified filesystem)
/bin -> /usr/bin         # Symbolic link
/sbin -> /usr/sbin       # Symbolic link

# Actual binary directories
/usr/bin                 # Main system binaries
/usr/sbin                # System administration binaries
/usr/local/bin           # Locally installed binaries
/usr/local/sbin          # Local system binaries

# User-specific binaries
/root/.local/bin         # Root user local binaries
/home/claude/.local/bin  # Claude user local binaries
/home/claude/.npm-global/bin  # NPM global binaries
```

---

## Environment-Specific Configurations

### Locale Settings
```bash
LANG=en_US.UTF-8
LC_ALL=en_US.UTF-8
```

### Timezone
```bash
TZ=UTC
```

### Shell Configuration
```bash
SHELL=/bin/bash
```

### Process Limits (ulimit)
```bash
ulimit -n 65536    # Open files
ulimit -u 32768    # Max processes
ulimit -c 0        # Core file size
ulimit -m unlimited # Memory
```

---

## Network Configuration

### DNS Resolution
```bash
# /etc/resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4
```

### Hosts File
```bash
# /etc/hosts
127.0.0.1   localhost
::1         localhost ip6-localhost ip6-loopback
```

---

## Special Tool Configurations

### ImageMagick Policy (Modified for PDF Support)
```xml
<!-- /etc/ImageMagick-6/policy.xml -->
<policy domain="coder" rights="read|write" pattern="PDF" />
<policy domain="resource" name="memory" value="256MiB"/>
<policy domain="resource" name="map" value="512MiB"/>
<policy domain="resource" name="width" value="16KP"/>
<policy domain="resource" name="height" value="16KP"/>
<policy domain="resource" name="area" value="128MP"/>
<policy domain="resource" name="disk" value="1GiB"/>
```

### Git Global Configuration
```ini
[user]
    name = Claude
    email = claude@anthropic.com
[init]
    defaultBranch = main
[core]
    editor = vim
```

### Jupyter Configuration
```python
# ~/.jupyter/jupyter_notebook_config.py
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.allow_root = True
c.NotebookApp.open_browser = False
```

---

## LaTeX Package Details

### Major LaTeX Packages Included
```
texlive-base
texlive-latex-base
texlive-latex-recommended
texlive-latex-extra
texlive-fonts-recommended
texlive-fonts-extra
texlive-science
texlive-pictures
texlive-bibtex-extra
texlive-lang-english
```

---

## Verification Commands

### Complete Environment Check Script
```bash
#!/bin/bash

echo "=== System Information ==="
uname -a
lsb_release -a 2>/dev/null

echo -e "\n=== Core Tools ==="
echo "Python: $(python3 --version)"
echo "Pip: $(pip3 --version)"
echo "Node: $(node --version)"
echo "NPM: $(npm --version)"
echo "Java: $(java --version 2>&1 | head -1)"
echo "GCC: $(gcc --version | head -1)"

echo -e "\n=== Document Tools ==="
command -v pandoc && pandoc --version | head -1
command -v soffice && soffice --version 2>&1 | head -1
command -v convert && convert --version | head -1
command -v pdflatex && pdflatex --version | head -1
command -v tesseract && tesseract --version 2>&1 | head -1

echo -e "\n=== Package Counts ==="
echo "Python packages: $(pip list 2>/dev/null | tail -n +3 | wc -l)"
echo "NPM global: $(npm list -g --depth=0 2>/dev/null | grep '^+--' | wc -l)"
echo "System packages: $(dpkg -l | grep '^ii' | wc -l)"
echo "Shared libraries: $(ldconfig -p 2>/dev/null | tail -n +2 | wc -l)"

echo -e "\n=== Directory Structure ==="
ls -la /mnt/
ls -la /home/claude/

echo -e "\n=== Python Paths ==="
python3 -c "import sys; print('\n'.join(sys.path))"

echo -e "\n=== NPM Configuration ==="
npm config list

echo -e "\n=== Environment Variables ==="
env | sort | grep -E '^(PATH|PYTHON|NODE|JAVA|HOME|USER)'
```

---

## Container Resource Recommendations

### Minimum Requirements
```yaml
resources:
  limits:
    memory: 4Gi
    cpu: 2
  requests:
    memory: 2Gi
    cpu: 1
```

### Recommended Requirements
```yaml
resources:
  limits:
    memory: 8Gi
    cpu: 4
  requests:
    memory: 4Gi
    cpu: 2
```

### Storage
```yaml
volumes:
  - name: skills
    size: 1Gi
  - name: knowledge
    size: 5Gi
  - name: user-data
    size: 10Gi
  - name: tmp
    size: 5Gi
```

---

## Known Quirks and Special Behaviors

1. **Unified /usr filesystem**: `/bin` and `/sbin` are symlinks to `/usr/bin` and `/usr/sbin`

2. **NPM Global Path**: Uses `/home/claude/.npm-global` instead of system-wide installation

3. **Python PIP**: Configured with `PIP_ROOT_USER_ACTION=ignore` to allow root installations

4. **LibreOffice**: Runs in headless mode only, no GUI components

5. **ImageMagick**: Policy modified to allow PDF operations (security consideration)

6. **Proxy Configuration**: Environment includes proxy settings that may need adjustment

7. **Playwright Browsers**: Not installed by default but path configured at `/opt/pw-browsers`

8. **Working Directory**: Default is `/home/claude`, not `/root`

9. **File System Case**: Case-sensitive filesystem

10. **Temp Directory**: `/tmp` with sticky bit (1777 permissions)

---

## Testing Checklist

- [ ] Python imports all major libraries without error
- [ ] NPM global commands are in PATH and executable
- [ ] Document conversion works (DOCX→PDF, PDF→Image, etc.)
- [ ] LaTeX compilation produces PDFs
- [ ] ImageMagick can process PDFs
- [ ] LibreOffice headless conversions work
- [ ] Tesseract OCR functions properly
- [ ] Git operations work
- [ ] File permissions allow read/write in work directories
- [ ] Skills files are accessible and readable
- [ ] Environment variables are properly set
- [ ] Locale and timezone are configured
- [ ] All paths in PATH variable are valid
- [ ] Package managers (pip, npm) can install new packages

---

This supplement provides the exact versions and configurations needed for precise replication of the Claude computer environment. Use this in conjunction with the main Docker replication guide and the environment inventory files for complete environment setup.
