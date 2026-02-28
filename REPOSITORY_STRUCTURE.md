# Repository Structure Overview

This template provides a standardized structure for all AI Application Engineering patterns.

## Directory Organization

### 📄 Root Level

- `README.md` - Main documentation (this serves as the template)
- `LICENSE` - MIT License
- `.gitignore` - Git ignore patterns

### 🏗️ `architecture/`

Contains all architecture documentation and diagrams:

- `system-overview.png` - High-level system architecture
- `data-flow.png` - Data flow diagram
- `design-decisions.md` - Architecture Decision Records (ADR)

### 📦 `deployment/`

Infrastructure as Code organized by tools:

- `bicep/` - Azure Bicep templates
- `terraform/` - Terraform modules
- `helm/` - Helm charts for Kubernetes
- `k8s/` - Raw Kubernetes manifests

### 💻 `app/`

Application source code:

- `src/` - Application implementation
- `tests/` - Unit and integration tests

### 📚 `workshop/`

Hands-on learning materials:

- `part1.md` - Foundation workshop (3-4 hours)
- `part2.md` - Advanced topics (4-5 hours)
- `validation-checklist.md` - Post-deployment validation

### 📖 `docs/`

Additional operational documentation:

- `security.md` - Security guidelines
- `production-hardening.md` - Production deployment checklist
- `troubleshooting.md` - Common issues and solutions
- `scalability.md` - Scaling patterns and guidelines

### 📊 `diagrams/`

Source files for architecture diagrams:

- `drawio/` - Draw.io editable diagram files

### ⚙️ `.github/`

GitHub-specific configuration:

- `ISSUE_TEMPLATE/` - Issue templates (bug_report.md, feature_request.md)
- `pull_request_template.md` - PR template
- `workflows/` - CI/CD pipelines (ci.yml)

## Using This Template

### Creating a New Pattern Repository

```bash
# 1. Create repository from template
# Use GitHub UI: "Use this template" button

# 2. Clone your new repository
git clone https://github.com/yourusername/your-pattern.git
cd your-pattern

# 3. Update placeholder content
# Edit README.md with your pattern details
# Update architecture diagrams
# Add your implementation code

# 4. Commit and push
git add .
git commit -m "Initial pattern implementation"
git push origin main
```

### Template Customization Checklist

When creating a new repository from this template:

- [ ] Update repository name
- [ ] Update README.md with pattern-specific content
- [ ] Add architecture diagrams to `architecture/`
- [ ] Create deployment templates in `deployment/`
- [ ] Add application code to `app/`
- [ ] Update workshop content in `workshop/`
- [ ] Customize GitHub workflows in `.github/workflows/`
- [ ] Update LICENSE if using different license

## Naming Conventions

All repositories in the AI Application Engineering Hub should follow consistent naming:

### Repository Names

Pattern: `<domain>-<component>-pattern`

Examples:
- `azure-iot-operations-edge-cloud-pattern`
- `ai-rag-application-pattern`
- `ai-agent-orchestration-pattern`

### Branch Names

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches

### Commit Messages

Format: `[type] description`

Types: feat, fix, docs, style, refactor, test, chore

Example: `[feat] Add MQTT broker configuration`

## Quality Standards

All patterns should meet these standards:

### Code Quality

- [ ] Follows consistent code style
- [ ] Includes unit tests
- [ ] Has integration tests
- [ ] Passes linting checks
- [ ] Documentation is complete

### Architecture Quality

- [ ] Clear system architecture
- [ ] Documented design decisions
- [ ] Data flow diagrams
- [ ] Component interactions defined
- [ ] Security considerations addressed

### Operational Quality

- [ ] Production deployment guide
- [ ] Monitoring and alerting setup
- [ ] Troubleshooting guide
- [ ] Disaster recovery plan
- [ ] Scaling guidelines

### Documentation Quality

- [ ] README is comprehensive
- [ ] Architecture diagrams are clear
- [ ] Workshop guides are structured
- [ ] Code is commented
- [ ] Links are working

## Related Templates

This template is part of the AI Application Engineering Hub.

For other patterns:
- [AI RAG Application Pattern](https://github.com/ai-app-engineering/ai-rag-application-pattern)
- [AI Agent Orchestration Pattern](https://github.com/ai-app-engineering/ai-agent-orchestration-pattern)
- [Template Hub Index](https://github.com/ai-app-engineering/ai-application-pattern-template)

## Support

For questions about this template:
- Check [README.md](README.md)
- Review [troubleshooting.md](docs/troubleshooting.md)
- Open a GitHub issue

---

**Last Updated:** 2026-02-28
**Version:** v1.0
