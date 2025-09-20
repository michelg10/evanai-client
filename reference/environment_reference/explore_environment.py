#!/usr/bin/env python3
"""
Claude Environment Capabilities Demo
This script demonstrates various capabilities available in the Claude computer environment.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_command(cmd):
    """Check if a command is available."""
    try:
        subprocess.run(['which', cmd], capture_output=True, check=True)
        return True
    except:
        return False

def get_python_packages():
    """Get a sample of interesting Python packages."""
    interesting_packages = [
        'pandas', 'numpy', 'matplotlib', 'scikit-learn', 'openpyxl',
        'beautifulsoup4', 'requests', 'flask', 'pytesseract', 'pillow',
        'reportlab', 'pypdf', 'python-pptx', 'camelot-py', 'plotly'
    ]
    
    result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], 
                          capture_output=True, text=True)
    installed = {pkg['name'].lower(): pkg['version'] 
                 for pkg in json.loads(result.stdout)}
    
    return {pkg: installed.get(pkg, 'Not installed') 
            for pkg in interesting_packages}

def explore_filesystem():
    """Explore key directories."""
    paths = {
        'Skills Directory': '/mnt/skills',
        'Knowledge Base': '/mnt/knowledge',
        'User Uploads': '/mnt/user-data/uploads',
        'Output Directory': '/mnt/user-data/outputs',
        'Working Directory': '/home/claude'
    }
    
    results = {}
    for name, path in paths.items():
        p = Path(path)
        if p.exists():
            if p.is_dir():
                file_count = len(list(p.glob('*')))
                results[name] = f"Exists ({file_count} items)"
            else:
                results[name] = "Exists (file)"
        else:
            results[name] = "Not found"
    
    return results

def check_tools():
    """Check for available command-line tools."""
    tools = {
        'Document Processing': ['pandoc', 'pdftotext', 'qpdf', 'soffice'],
        'Image Processing': ['convert', 'pdftoppm', 'pdfimages'],
        'Development': ['git', 'gcc', 'make', 'node', 'npm'],
        'Web Tools': ['curl', 'wget'],
        'LaTeX': ['pdflatex', 'latex']
    }
    
    results = {}
    for category, commands in tools.items():
        available = [cmd for cmd in commands if check_command(cmd)]
        results[category] = available
    
    return results

def main():
    """Run all checks and display results."""
    print("=" * 60)
    print("CLAUDE ENVIRONMENT CAPABILITIES EXPLORER")
    print("=" * 60)
    
    # System Info
    print("\n📊 SYSTEM INFORMATION")
    print("-" * 40)
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print(f"Current Directory: {os.getcwd()}")
    
    # Filesystem
    print("\n📁 FILESYSTEM EXPLORATION")
    print("-" * 40)
    fs_results = explore_filesystem()
    for name, status in fs_results.items():
        print(f"  {name}: {status}")
    
    # Command-line tools
    print("\n🔧 AVAILABLE TOOLS")
    print("-" * 40)
    tools = check_tools()
    for category, available in tools.items():
        if available:
            print(f"  {category}: {', '.join(available)}")
    
    # Python packages
    print("\n📦 KEY PYTHON PACKAGES")
    print("-" * 40)
    packages = get_python_packages()
    for pkg, version in packages.items():
        if version != 'Not installed':
            print(f"  ✓ {pkg}: {version}")
    
    # NPM packages
    print("\n📦 NPM GLOBAL PACKAGES (Sample)")
    print("-" * 40)
    try:
        result = subprocess.run(['npm', 'list', '-g', '--depth=0'], 
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')[1:11]  # First 10 packages
        for line in lines:
            if line.strip() and line.startswith('+--'):
                print(f"  {line.replace('+--', '✓')}")
    except:
        print("  Unable to list NPM packages")
    
    # Skills available
    print("\n📚 DOCUMENT SKILLS AVAILABLE")
    print("-" * 40)
    skills_path = Path('/mnt/skills/public')
    if skills_path.exists():
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / 'SKILL.md'
                if skill_file.exists():
                    print(f"  ✓ {skill_dir.name.upper()} skill")
    
    print("\n" + "=" * 60)
    print("EXPLORATION COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
