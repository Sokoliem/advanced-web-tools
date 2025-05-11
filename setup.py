from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="claude-mcp-scaffold",
    version="0.1.0",
    description="A scaffold for Claude's Model Control Protocol with web browsing capabilities",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[req for req in requirements if not req.startswith('#')],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "flake8>=6.1.0",
            "mypy>=1.5.1",
            "black>=23.7.0",
        ],
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "claude-mcp=claude_mcp_scaffold.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)