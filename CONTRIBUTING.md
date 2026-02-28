# Contributing to AI Application Engineering Hub

Thank you for your interest in contributing to this pattern! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### 1. Report Issues

- Check if the issue already exists
- Provide clear description
- Include reproduction steps
- Share relevant logs

### 2. Suggest Enhancements

- Describe the enhancement
- Explain the use case
- Discuss potential alternatives
- Submit as feature request

### 3. Submit Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Write tests
5. Update documentation
6. Commit: `git commit -m "[feat] Add my feature"`
7. Push: `git push origin feature/my-feature`
8. Open a Pull Request

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No hardcoded secrets

### PR Title Format

`[type] description`

Examples:
- `[feat] Add MQTT broker configuration`
- `[fix] Fix data flow initialization`
- `[docs] Update deployment guide`

### PR Description

Include:
- What problem does this solve?
- How does this change work?
- Are there any side effects?
- Related issues/PRs

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/this-repo.git
cd this-repo

# Create virtual environment (if Python)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run linter
pylint app/

# Run type checks
mypy app/
```

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### End-to-End Tests

```bash
pytest tests/e2e/
```

### Coverage

```bash
pytest --cov=app tests/
```

## Documentation Standards

### Code Comments

- Comment **why**, not **what**
- Keep comments up to date
- Use clear language

### Docstrings

```python
def function_name(param1, param2):
    """
    Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this occurs
    """
```

### Markdown Files

- Use clear headings
- Include code examples
- Provide links to related docs
- Keep lines under 120 characters

## Commit Message Conventions

### Format

```
[type] subject

body (optional)

footer (optional)
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation
- **style**: Code style (formatting, missing semicolons, etc)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Build process, dependencies, etc

### Examples

```
[feat] Add MQTT broker configuration

- Implement broker setup
- Add TLS support
- Include validation

Closes #123
```

## Review Process

1. Automated checks pass (CI/CD)
2. Code review (at least 1 maintainer)
3. All feedback addressed
4. Approved and merged

## Maintainer Guidelines

### Code Review Checklist

- [ ] Code follows style guide
- [ ] Tests are adequate
- [ ] Documentation is clear
- [ ] No security issues
- [ ] Performance is acceptable
- [ ] Backward compatible or migration path

### Merge Squash/Rebase

- Squash: Multiple commits into one
- Rebase: Keep commit history clean

## Release Process

1. Update version in `package.json` / `setup.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release

## Questions?

- Open a discussion in GitHub
- Email: [maintainer@example.com](mailto:maintainer@example.com)
- Check [documentation](./docs)

---

**Thank you for contributing!**
