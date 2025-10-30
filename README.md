# Inventory Management System (IMS)

## Project Status: CI/CD Skeleton Only

This repository contains the **project skeleton structure** and **CI/CD pipeline** for the Command-Line Inventory Management System course project.

⚠️ **Important:** Business logic and application features are NOT yet implemented. This is the foundational structure with placeholder modules.

---

## 📋 Project Overview

A command-line inventory management system built with Python, designed following Software Engineering best practices with automated CI/CD pipeline.

**Tech Stack:**
- Python 3.10+
- pytest (testing framework)
- pytest-cov (code coverage)
- pylint (code quality)
- bandit (security scanning)
- SQLite (database - placeholder)
- GitHub Actions (CI/CD)

---

## 📂 Repository Structure

```
ims/
├── .github/
│   └── workflows/
│       └── ci.yml              # 5-stage CI/CD pipeline
├── src/
│   ├── cli.py                  # CLI interface (placeholder)
│   ├── product_manager.py      # Product operations (placeholder)
│   ├── order_processor.py      # Order processing (placeholder)
│   ├── supplier_manager.py     # Supplier management (placeholder)
│   ├── storage.py              # Database operations (placeholder)
│   ├── backup_security.py      # Backup & security (placeholder)
│   ├── auth.py                 # Authentication (placeholder)
│   ├── logger.py               # Logging (placeholder)
│   └── config.py               # Configuration (placeholder)
├── tests/
│   ├── unit/                   # Unit tests (placeholders)
│   ├── integration/            # Integration tests (placeholders)
│   └── system/                 # System tests (placeholders)
├── data/
│   └── database.sqlite         # Database file (empty)
├── backups/                    # Backup storage
├── reports/                    # Generated reports
├── docs/
│   ├── README_CI.md            # CI/CD documentation
│   └── RETROSPECTIVE.md        # Sprint retrospectives
├── scripts/
│   └── package_deploy.sh       # Deployment script (placeholder)
├── .pylintrc                   # Pylint configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── .gitignore                  # Git ignore rules
├── LICENSE                     # Project license
└── README.md                   # This file
```

---

## 🚀 CI/CD Pipeline

The project includes a **5-stage sequential GitHub Actions pipeline** that ensures code quality:

### Pipeline Stages

1. **Build** - Environment setup and dependency installation
2. **Test** - Run ALL test cases (unit + integration + system)
3. **Coverage** - Analyze code coverage (minimum 75%)
4. **Lint** - Code quality check with pylint (minimum score 7.5/10)
5. **Security** - Security scanning with Bandit

### Pipeline Triggers

- Push to any branch
- Pull request to `main`

### Quality Gates

| Stage | Threshold | Status |
|-------|-----------|--------|
| Tests | 100% pass | ✅ Enforced |
| Coverage | ≥ 75% | ✅ Enforced |
| Lint | ≥ 7.5/10 | ✅ Enforced |
| Security | 0 high severity | ✅ Enforced |

For detailed CI/CD information, see [`docs/README_CI.md`](docs/README_CI.md).

---

## 🛠️ Local Development

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd ims

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=html tests/
```

### Code Quality Checks

```bash
# Run pylint
pylint src/

# Run security scan
bandit -r src/
```

---

## 📝 Current Status

**Implemented:**
- ✅ Complete folder structure
- ✅ Placeholder modules for all components
- ✅ 5-stage CI/CD pipeline
- ✅ Test framework setup
- ✅ Code quality tools configuration
- ✅ Documentation structure

**Not Implemented (Future Sprints):**
- ⏳ Business logic for all modules
- ⏳ Database schema and operations
- ⏳ User authentication
- ⏳ CLI command handlers
- ⏳ Report generation
- ⏳ Backup/restore functionality
- ⏳ Comprehensive test cases

---

## 📖 Documentation

- **CI/CD Guide:** [`docs/README_CI.md`](docs/README_CI.md)
- **Retrospectives:** [`docs/RETROSPECTIVE.md`](docs/RETROSPECTIVE.md)

---

## 🤝 Contributing

This is a course project. Contributions follow the academic integrity guidelines of the institution.

---

## 📄 License

See [`LICENSE`](LICENSE) file for details.

---

## 👨‍💻 Author

Course Project - Software Engineering  
Implementation planned in iterative sprints

---

## 🎯 Next Steps

1. Implement core business logic in src/ modules
2. Write comprehensive unit tests
3. Add integration tests for module interactions
4. Implement system tests for end-to-end workflows
5. Achieve >75% code coverage
6. Maintain pylint score >7.5
7. Document retrospectives after each sprint

---

**Note:** This skeleton demonstrates CI/CD setup and project structure. Application logic will be implemented incrementally following agile methodology.
