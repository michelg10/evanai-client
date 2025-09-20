# Claude Computer Environment Exploration Report

## System Information
- **Operating System**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Architecture**: Linux-based container environment
- **Home Directory**: `/home/claude`
- **Working Directory**: `/home/claude` (recommended for all work)

## File System Structure

### Key Directories
1. **`/mnt/user-data/`**
   - `uploads/` - Files you upload are accessible here
   - `outputs/` - Final files to share with users go here
   
2. **`/mnt/skills/`**
   - Contains specialized skill files for various tasks
   - Document creation skills (DOCX, PPTX, XLSX, PDF)
   - Each skill includes detailed instructions and scripts
   
3. **`/mnt/knowledge/`**
   - Personal knowledge base that persists across conversations
   - Private to your account
   - Can store notes, scripts, and configurations

## Available Development Tools

### Programming Languages
- **Python 3** - Full Python environment with pip
- **Node.js** - JavaScript runtime with npm
- **GCC** - C/C++ compiler
- **Make** - Build automation tool
- **Git** - Version control

### Document Processing Tools
- **Pandoc** - Universal document converter
- **LibreOffice** - Office suite (headless mode for conversions)
- **ImageMagick** - Image manipulation (`convert` command)
- **Poppler Utils** - PDF utilities (pdftotext, pdfimages, pdftoppm)
- **LaTeX** - Document preparation system (pdflatex, etc.)
- **QPDF** - PDF transformation tools

## Installed Python Libraries

### Data Science & Analysis
- **pandas** 2.3.2 - Data manipulation and analysis
- **numpy** 2.3.3 - Numerical computing
- **matplotlib** 3.10.6 - Plotting and visualization
- **seaborn** 0.13.2 - Statistical data visualization
- **scikit-learn** 1.7.2 - Machine learning library
- **scikit-image** 0.25.2 - Image processing

### Document Processing
- **openpyxl** - Excel file manipulation
- **python-pptx** - PowerPoint file manipulation
- **pypdf** - PDF processing
- **pdfplumber** - PDF text and table extraction
- **camelot-py** - Table extraction from PDFs
- **pytesseract** - OCR capabilities
- **reportlab** - PDF generation
- **markitdown** - Markdown conversion

### Web & API
- **requests** - HTTP library
- **beautifulsoup4** - Web scraping
- **flask** - Web framework
- **fastapi** - Modern web API framework

## Installed NPM Packages (Global)

### Document Creation
- **docx** 9.5.1 - Create Word documents
- **pptxgenjs** 4.0.1 - Create PowerPoint presentations
- **pdf-lib** 1.17.1 - Create and modify PDF documents
- **sharp** 0.34.3 - Image processing

### Web Development
- **react** 19.1.1 - UI library
- **react-dom** 19.1.1 - React DOM
- **react-icons** 5.5.0 - Icon library
- **playwright** 1.55.0 - Browser automation

### Markdown Tools
- **marked** 16.3.0 - Markdown parser
- **markdown-pdf** 11.0.0 - Convert Markdown to PDF
- **markdown-toc** 1.2.0 - Generate table of contents
- **markdownlint-cli** 0.45.0 - Markdown linting
- **remark-cli** 12.0.1 - Markdown processor

### Other Tools
- **@mermaid-js/mermaid-cli** 11.10.1 - Create diagrams from text
- **ts-node** 10.9.2 - TypeScript execution
- **tsx** 4.20.5 - TypeScript execute and REPL

## Web Tools
- **wget** - Web content downloader
- **curl** - Data transfer tool

## Special Features

### Document Skills System
The `/mnt/skills/public/` directory contains comprehensive guides for:
- Creating and editing Word documents (with tracked changes support)
- Building PowerPoint presentations (from scratch or templates)
- Generating Excel spreadsheets (with formulas and formatting)
- Processing PDFs (extraction, merging, form filling)

Each skill includes:
- Detailed workflows
- Code examples
- Helper scripts
- Best practices
- Dependencies list

### Persistent Knowledge Base
The `/mnt/knowledge/` directory provides:
- Persistence across all conversations
- Private to your account
- Ability to build a growing knowledge base
- Store custom scripts and configurations

### File Workflow Pattern
1. Upload files → Available at `/mnt/user-data/uploads/`
2. Work on files → Use `/home/claude/` as workspace
3. Share outputs → Copy to `/mnt/user-data/outputs/`
4. Provide links → Use `computer:///mnt/user-data/outputs/filename`

## Interesting Capabilities

### Document Conversions
- DOCX ↔ PDF ↔ Markdown ↔ HTML
- PPTX → PDF → Images
- Excel ↔ CSV ↔ JSON
- OCR for scanned documents

### Data Processing
- Full pandas/numpy stack for data analysis
- Machine learning with scikit-learn
- Image processing with PIL/scikit-image
- Visualization with matplotlib/seaborn

### Automation
- Web scraping with BeautifulSoup
- Browser automation with Playwright
- API development with FastAPI/Flask
- Task automation with Python/Node.js

### Development
- Full Python development environment
- Node.js/TypeScript support
- C/C++ compilation
- Git for version control
- Multiple package managers (pip, npm)

## Notable Limitations
- No persistent storage between separate conversations (except `/mnt/knowledge/`)
- No GUI applications (headless environment)
- No Docker/containerization tools
- No cloud CLI tools (AWS, GCloud, etc.)
- Limited browser capabilities (no Chromium/Firefox)

## Tips for Effective Use
1. Use the skills directory for complex document tasks
2. Leverage the persistent knowledge directory for long-term storage
3. Utilize the comprehensive Python/Node.js libraries for data processing
4. Take advantage of document conversion tools for format flexibility
5. Use the proper file workflow (uploads → work → outputs) for clarity
