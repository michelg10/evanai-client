# Claude Environment Docker Replication

This directory contains a complete Docker-based replication of the Claude computer environment based on the reference documentation. The environment includes Ubuntu 24.04 LTS with Python 3.12.3, Node.js 18.19.1, and comprehensive document processing capabilities.

## Overview

The environment replicates Claude's computing environment with:
- **OS**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Python**: 3.12.3 with extensive data science and document processing libraries
- **Node.js**: 18.19.1 with TypeScript and modern web development tools
- **Java**: OpenJDK 21 for enterprise applications
- **Document Processing**: Full LaTeX, LibreOffice, Pandoc, ImageMagick suite
- **OCR**: Tesseract with all language packs
- **Media**: FFmpeg with extensive codec support

## Quick Start

### Prerequisites
- Docker installed and running
- At least 8GB of available RAM
- ~15GB of disk space for the image

### Build the Image

```bash
# Make scripts executable
chmod +x build.sh verify.sh

# Build the Docker image
./build.sh

# Or build without cache
./build.sh --no-cache

# Build with custom tag
./build.sh --tag dev --verbose
```

### Run the Container

#### Option 1: Direct Docker Run
```bash
# Interactive shell
docker run -it --rm claude-environment:latest

# With volume mounts
docker run -it --rm \
  -v $(pwd)/workspace:/home/claude/workspace \
  -v $(pwd)/skills:/mnt/skills \
  -v $(pwd)/knowledge:/mnt/knowledge \
  claude-environment:latest
```

#### Option 2: Docker Compose
```bash
# Start the environment
docker-compose up -d

# Access the container
docker-compose exec claude-environment bash

# Start with Jupyter notebook
docker-compose --profile jupyter up jupyter
```

### Verify Installation

```bash
# Run verification script
./verify.sh

# Verify specific image
./verify.sh my-image:tag --verbose

# Or run verification inside container
docker run --rm claude-environment:latest /verify_environment.sh
```

## Directory Structure

The container creates the following directory structure:

```
/home/claude/          # Main working directory
├── .npm-global/       # NPM global packages
├── .cache/            # Cache directories
├── .config/           # Configuration files
└── workspace/         # Your working files

/mnt/
├── user-data/         # User uploads and outputs
│   ├── uploads/
│   └── outputs/
├── skills/            # Skills repository
│   └── public/
│       ├── docx/
│       ├── pdf/
│       ├── pptx/
│       └── xlsx/
└── knowledge/         # Knowledge base
```

## Features

### Python Environment
- **Data Science**: NumPy, Pandas, SciPy, scikit-learn, statsmodels
- **Visualization**: Matplotlib, Seaborn, Plotly, Bokeh, Altair
- **Document Processing**: PyPDF, python-docx, python-pptx, openpyxl, reportlab
- **Web Development**: Flask, FastAPI, Django, requests, BeautifulSoup
- **Development Tools**: Jupyter, IPython, Black, pytest, mypy

### Node.js Environment
- **TypeScript**: Full TypeScript toolchain with ts-node
- **Web Frameworks**: React, Vue.js (via CDN)
- **Document Creation**: docx, pptxgenjs, pdf-lib
- **Markdown Tools**: Complete markdown processing suite
- **Build Tools**: Webpack (via npx), various transpilers

### Document Processing
- **Pandoc**: Universal document converter
- **LaTeX**: Full TeX Live distribution
- **LibreOffice**: Headless document conversion
- **ImageMagick**: Image manipulation with PDF support
- **Tesseract**: OCR with all language packs
- **FFmpeg**: Audio/video processing

## Docker Compose Services

### Main Environment
The default service providing the full Claude environment.

```bash
docker-compose up -d claude-environment
```

### Jupyter Notebook (Optional)
A Jupyter notebook server for interactive development.

```bash
# Start Jupyter (accessible at http://localhost:8888)
docker-compose --profile jupyter up jupyter
```

## Configuration

### Environment Variables
Key environment variables are pre-configured:
- `PYTHONUNBUFFERED=1` - Unbuffered Python output
- `IS_SANDBOX=yes` - Sandbox mode indicator
- `JAVA_HOME` - Java installation path
- `NODE_PATH` - Node module paths
- `NPM_CONFIG_PREFIX` - NPM global directory

### Resource Limits
Default resource limits in docker-compose.yml:
- Memory: 8GB limit, 4GB reservation
- CPUs: 4 cores limit, 2 cores reservation
- Shared memory: 2GB (for ML workloads)

Adjust these in docker-compose.yml based on your system.

## Customization

### Adding Skills Files
Place your skills files in the appropriate directories:
```bash
./skills/public/docx/   # Word templates
./skills/public/pdf/    # PDF templates
./skills/public/pptx/   # PowerPoint templates
./skills/public/xlsx/   # Excel templates
```

### Installing Additional Packages

#### Python Packages
```bash
# Inside container
pip install package-name

# Or add to requirements.txt and rebuild
echo "package-name==1.0.0" >> requirements.txt
./build.sh --no-cache
```

#### NPM Packages
```bash
# Inside container
npm install -g package-name

# Or add to Dockerfile and rebuild
```

### Extending the Image
Create a new Dockerfile:
```dockerfile
FROM claude-environment:latest

# Add your customizations
RUN pip install your-packages
COPY your-files /destination/

# Set your working directory
WORKDIR /your/workspace
```

## Troubleshooting

### Build Issues

1. **Out of disk space**: The full image is ~10-15GB. Ensure sufficient space.
   ```bash
   docker system prune -a  # Clean Docker cache
   ```

2. **Network timeouts**: Use local package mirrors or increase timeouts.

3. **Permission errors**: Ensure Docker has proper permissions.

### Runtime Issues

1. **ImageMagick PDF errors**: Check policy file is correctly modified.
   ```bash
   docker exec <container> cat /etc/ImageMagick-6/policy.xml | grep PDF
   ```

2. **Node module not found**: Verify NODE_PATH is set correctly.
   ```bash
   docker exec <container> npm list -g
   ```

3. **Python import errors**: Check package installation.
   ```bash
   docker exec <container> pip list | grep package-name
   ```

### Performance

For better performance:
- Allocate more RAM to Docker
- Use volume mounts for large datasets
- Enable BuildKit for faster builds:
  ```bash
  DOCKER_BUILDKIT=1 docker build .
  ```

## Differences from Original Environment

Minor differences from the reference environment:
- Running as root user (original may have different user setup)
- No proxy configuration by default (add if needed)
- Playwright browsers optional (uncomment in Dockerfile if needed)
- Some system services not available (systemd, cron, etc.)

## Maintenance

### Updating Packages

```bash
# Check for Python package updates
docker run --rm claude-environment:latest pip list --outdated

# Check for NPM updates
docker run --rm claude-environment:latest npm outdated -g

# Check for system updates
docker run --rm claude-environment:latest apt list --upgradable
```

### Rebuilding

Rebuild periodically to get security updates:
```bash
./build.sh --no-cache --tag $(date +%Y%m%d)
```

## Support

For issues or questions:
1. Check the verification script output: `./verify.sh --verbose`
2. Review the reference documentation in `/reference/environment_reference/`
3. Examine container logs: `docker logs <container-id>`

## License

This Docker environment is provided as-is for development purposes. Please ensure compliance with all software licenses for the included packages.