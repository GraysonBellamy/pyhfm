# Contributing

We welcome contributions to pyhfm! This guide will help you get started with contributing to the project.

## Getting Started

### Development Setup

1. **Fork and clone the repository**:
```bash
git clone https://github.com/yourusername/pyhfm.git
cd pyhfm
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**:
```bash
pip install -e ".[dev,test]"
```

4. **Install pre-commit hooks**:
```bash
pre-commit install
```

### Development Workflow

1. **Create a feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following the guidelines below

3. **Run tests and checks**:
```bash
# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy src/pyhfm

# Run formatting
ruff format .
```

4. **Commit your changes**:
```bash
git add .
git commit -m "feat: add your feature description"
```

5. **Push and create a pull request**:
```bash
git push origin feature/your-feature-name
```

## Development Guidelines

### Code Style

We use several tools to maintain code quality:

- **Ruff**: For linting and formatting
- **MyPy**: For type checking
- **Pre-commit**: For automated checks

#### Code Formatting

```bash
# Format all code
ruff format .

# Check for linting issues
ruff check .

# Fix auto-fixable issues
ruff check . --fix
```

#### Type Annotations

All new code should include type annotations:

```python
from typing import Optional, Dict, Any
import pyarrow as pa

def read_hfm(
    filename: str,
    return_metadata: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> pa.Table:
    """Read HFM file with proper type annotations."""
    ...
```

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/pyhfm --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_read_thermal_conductivity
```

#### Writing Tests

Place tests in the `tests/` directory with descriptive names:

```python
import pytest
import pyhfm
from pathlib import Path

def test_read_thermal_conductivity_file():
    """Test reading a thermal conductivity HFM file."""
    # Arrange
    test_file = Path("tests/data/thermal_conductivity.tst")

    # Act
    table = pyhfm.read_hfm(test_file)

    # Assert
    assert table.num_rows > 0
    assert "upper_thermal_conductivity" in table.column_names
```

#### Test Data

- Place test files in `tests/data/`
- Use small, representative files
- Anonymize any real measurement data
- Document the origin and characteristics of test files

### Documentation

#### Docstrings

Use Google-style docstrings:

```python
def read_hfm(filename: str, return_metadata: bool = False) -> pa.Table:
    """Read HFM data file and return PyArrow table.

    Args:
        filename: Path to the HFM file to read.
        return_metadata: If True, return metadata along with data.

    Returns:
        PyArrow table containing the measurement data.

    Raises:
        HFMFileError: If the file cannot be read.
        HFMParsingError: If the file format is invalid.

    Example:
        >>> table = read_hfm("sample.tst")
        >>> df = table.to_polars()
    """
```

#### API Documentation

The API documentation is generated automatically from docstrings using MkDocs and mkdocstrings. Make sure your docstrings are comprehensive and include examples.

#### README Updates

Update the README.md when adding new features or changing the API.

## Project Architecture

### Package Structure

```
pyhfm/
├── src/pyhfm/
│   ├── api/           # High-level user API
│   │   ├── __init__.py
│   │   └── loaders.py # Main read_hfm function and CLI
│   ├── core/          # Core parsing logic
│   │   ├── __init__.py
│   │   └── parser.py  # HFMParser class
│   ├── extractors/    # Data extraction components
│   │   ├── __init__.py
│   │   └── data_extractor.py
│   ├── __init__.py    # Public API exports
│   ├── constants.py   # Configuration and constants
│   ├── exceptions.py  # Custom exceptions
│   └── utils.py       # Utility functions
├── tests/             # Test suite
├── docs/              # Documentation source
└── examples/          # Usage examples
```

### Design Principles

1. **Simple API**: Keep the public API minimal and intuitive
2. **Type Safety**: Use type annotations throughout
3. **Error Handling**: Provide clear, specific error messages
4. **Performance**: Efficient memory usage with PyArrow
5. **Extensibility**: Modular design for easy extension

## Contribution Types

### Bug Fixes

1. **Identify the issue**: Look for existing issues or create a new one
2. **Write a failing test**: Reproduce the bug in a test
3. **Fix the bug**: Implement the minimal fix
4. **Verify the fix**: Ensure tests pass and no regressions

### New Features

1. **Discuss first**: Open an issue to discuss the feature before implementing
2. **Design the API**: Consider how it fits with existing functionality
3. **Implement with tests**: Include comprehensive test coverage
4. **Document**: Add docstrings and update documentation
5. **Examples**: Provide usage examples

### Documentation Improvements

- Fix typos and improve clarity
- Add examples and use cases
- Improve API documentation
- Update troubleshooting guides

### Performance Improvements

- Profile code to identify bottlenecks
- Implement optimizations with benchmarks
- Ensure improvements don't break existing functionality
- Document performance characteristics

## Commit Guidelines

### Commit Messages

Use conventional commit format:

```
type(scope): description

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Examples:
```
feat(parser): add support for UTF-8 encoded files

Add automatic encoding detection and fallback to UTF-8
when UTF-16LE fails.

Closes #123
```

```
fix(extractor): handle missing temperature data

Previously would crash when temperature columns were
missing from the file metadata.
```

### Pull Request Guidelines

1. **Clear title and description**: Explain what and why
2. **Link related issues**: Use "Closes #123" or "Fixes #123"
3. **Keep changes focused**: One feature/fix per PR
4. **Include tests**: All new code should have tests
5. **Update documentation**: If needed for the changes

## Code Review Process

### For Contributors

- Respond to reviewer feedback promptly
- Make requested changes in new commits (don't force-push)
- Ask questions if feedback is unclear

### For Reviewers

- Be constructive and specific in feedback
- Suggest improvements, don't just point out problems
- Consider the bigger picture and project goals
- Test the changes locally if possible

## Release Process

### Version Numbers

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Create release PR
5. Tag release after merge
6. Publish to PyPI

## Getting Help

### Community

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Don't hesitate to ask for early feedback

### Maintainer Contact

For urgent issues or private concerns, contact the maintainers through GitHub.

## Recognition

All contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes for their contributions
- GitHub contributors page

## License

By contributing to pyhfm, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to pyhfm! 🎉
