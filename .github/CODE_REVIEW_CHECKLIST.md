# Code Review Checklist

Use this checklist when reviewing pull requests.

## Automated Checks

- [ ] All CI/CD checks pass (GitHub Actions)
- [ ] Pre-commit hooks pass
- [ ] Code coverage maintained or improved
- [ ] No new linting errors
- [ ] No type checking errors

## Code Quality

### Style & Formatting

- [ ] Code follows Black formatting (100 char line length)
- [ ] Imports are properly sorted (isort via Ruff)
- [ ] No unnecessary whitespace or formatting issues
- [ ] Consistent naming conventions (snake_case for functions/variables)

### Type Hints

- [ ] All functions have complete type hints
- [ ] Return types are specified
- [ ] Modern Python 3.10+ syntax used (`list[str]`, `str | None`)
- [ ] No use of `Any` without justification
- [ ] Type hints are accurate and meaningful

### Documentation

- [ ] All public functions have docstrings
- [ ] Docstrings follow Google style
- [ ] Args, Returns, Raises sections are complete
- [ ] Complex logic has inline comments
- [ ] README updated if needed
- [ ] CHANGELOG updated if needed

### Code Structure

- [ ] Functions are focused and single-purpose
- [ ] No unnecessary complexity
- [ ] DRY principle followed (no code duplication)
- [ ] Appropriate use of Python 3.10+ features
- [ ] No overly long functions (>50 lines should be rare)

## Functionality

### Correctness

- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs or logic errors

### Testing

- [ ] New features have tests
- [ ] Bug fixes have regression tests
- [ ] Tests are meaningful and comprehensive
- [ ] Test names clearly describe what they test
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] No flaky tests

### Performance

- [ ] No obvious performance issues
- [ ] Appropriate data structures used
- [ ] No unnecessary loops or operations
- [ ] Large files handled efficiently (streaming if needed)

## Security

### Input Validation

- [ ] All user inputs are validated
- [ ] Regex patterns are safe (no ReDoS vulnerabilities)
- [ ] File paths are validated
- [ ] No SQL injection risks (if applicable)

### Data Handling

- [ ] No sensitive data in logs
- [ ] No credentials in code
- [ ] Mapping files handled securely
- [ ] No information leakage in error messages

### Dependencies

- [ ] No new dependencies without justification
- [ ] Dependencies are from trusted sources
- [ ] Version constraints are appropriate

## Compatibility

### Python Versions

- [ ] Works with Python 3.10+
- [ ] No use of deprecated features
- [ ] Modern syntax used appropriately

### Breaking Changes

- [ ] Breaking changes are documented
- [ ] Migration guide provided if needed
- [ ] Version number updated appropriately

## Best Practices

### Modern Python

- [ ] Pattern matching used where appropriate
- [ ] Walrus operator used where it improves readability
- [ ] Union types (`|`) instead of `Optional`
- [ ] Built-in generics (`list`, `dict`) instead of `typing` versions

### Error Handling

- [ ] Exceptions are specific (not bare `except:`)
- [ ] Error messages are helpful
- [ ] Resources are cleaned up properly
- [ ] Context managers used where appropriate

### Maintainability

- [ ] Code is self-documenting
- [ ] Magic numbers are avoided (use constants)
- [ ] Configuration is externalized
- [ ] No hardcoded values that should be configurable

## Specific to CloudMask

### Anonymization

- [ ] Deterministic hashing works correctly
- [ ] Prefixes are preserved when configured
- [ ] Mapping is complete and reversible
- [ ] No collisions in generated IDs

### Configuration

- [ ] Config changes are backwards compatible
- [ ] Default values are sensible
- [ ] Config validation works

### CLI

- [ ] Help text is clear and accurate
- [ ] Error messages are user-friendly
- [ ] Exit codes are appropriate
- [ ] Clipboard operations work correctly

## Review Comments

### Providing Feedback

- Be constructive and specific
- Explain the "why" behind suggestions
- Distinguish between "must fix" and "nice to have"
- Acknowledge good code and improvements
- Link to relevant documentation

### Example Comments

Good:
> "Consider using a context manager here to ensure the file is closed even if an exception occurs. See [PEP 343](https://www.python.org/dev/peps/pep-0343/)."

Bad:
> "This is wrong."

## Approval Criteria

Approve if:
- [ ] All automated checks pass
- [ ] No major issues found
- [ ] Minor issues are documented as comments
- [ ] Code improves the project

Request changes if:
- [ ] Automated checks fail
- [ ] Major bugs or security issues found
- [ ] Code quality significantly below standards
- [ ] Missing tests for new features

## After Approval

- [ ] Squash commits if needed
- [ ] Ensure commit message is clear
- [ ] Verify CI passes one final time
- [ ] Merge using appropriate strategy

## Resources

- [CODE_QUALITY.md](../../CODE_QUALITY.md) - Code quality standards
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines
- [Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
