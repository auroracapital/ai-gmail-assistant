# Contributing to AI Gmail Assistant

Thank you for your interest in contributing to AI Gmail Assistant! We welcome contributions from the community.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- Gmail account for testing
- OpenRouter API key

### Development Setup

1. **Fork the repository**

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-gmail-assistant.git
   cd ai-gmail-assistant
   ```

3. **Create a virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

6. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Code Standards

### Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 100 characters max
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Organized with `isort`

### Formatting

Before committing, format your code:

```bash
# Format with black
black src/

# Sort imports
isort src/

# Check linting
flake8 src/
```

### Type Hints

Use type hints for function signatures:

```python
def categorize_email(email: dict, context: str) -> dict:
    """Categorize email using AI."""
    ...
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_gmail_organizer.py
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test function names: `test_categorize_email_with_spam()`
- Mock external API calls (Gmail, OpenRouter)

Example:

```python
def test_categorize_email_as_spam():
    """Test that spam emails are correctly categorized."""
    email = {
        "subject": "You won the lottery!",
        "sender": "spam@example.com",
        "body": "Click here to claim your prize..."
    }
    result = categorize_email(email)
    assert result["action"] == "delete"
    assert "spam" in result["reason"].lower()
```

## 📋 Commit Guidelines

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:

```
feat(categorization): add support for Spanish language detection

- Detect Spanish emails using language detection library
- Generate Spanish draft responses
- Update tests for Spanish language support

Closes #42
```

```
fix(draft): prevent duplicate draft creation

- Check for existing drafts before creating new ones
- Delete old drafts in the same thread
- Add test for draft deduplication

Fixes #38
```

## 🔄 Pull Request Process

1. **Update documentation** if you've changed functionality
2. **Add tests** for new features
3. **Ensure all tests pass**: `pytest tests/`
4. **Format code**: `black src/ && isort src/`
5. **Update CHANGELOG.md** with your changes
6. **Create pull request** with a clear title and description

### PR Title Format

```
<type>: <description>
```

Examples:
- `feat: Add Microsoft Outlook support`
- `fix: Resolve duplicate draft creation bug`
- `docs: Update AWS deployment guide`

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2
- Change 3

## Testing
How was this tested?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted with black
- [ ] All tests passing
- [ ] CHANGELOG.md updated
```

## 🐛 Reporting Bugs

Use the [Bug Report template](https://github.com/yourusername/ai-gmail-assistant/issues/new?template=bug_report.md)

Include:
- **Description**: Clear description of the bug
- **Steps to reproduce**: Detailed steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, etc.
- **Logs**: Relevant error messages or logs

## 💡 Suggesting Features

Use the [Feature Request template](https://github.com/yourusername/ai-gmail-assistant/issues/new?template=feature_request.md)

Include:
- **Problem**: What problem does this solve?
- **Solution**: Proposed solution
- **Alternatives**: Alternative solutions considered
- **Use case**: Real-world use case

## 🔒 Security

**Do NOT** open public issues for security vulnerabilities.

Instead, email sam@auroracapital.nl with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- CHANGELOG.md for their contributions
- GitHub contributors page

## 💬 Questions?

- Join our [Discussions](https://github.com/yourusername/ai-gmail-assistant/discussions)
- Ask in the `#contributors` channel
- Email: contributors@ai-gmail-assistant.com

---

Thank you for contributing to AI Gmail Assistant! 🎉
