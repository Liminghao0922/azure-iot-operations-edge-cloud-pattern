# AI Application Pattern 快速参考指南

## 🎯 项目概览

这是一个**企业级AI应用工程模式库**的标准化模板。

**定位:** 不是Demo，不是玩具，而是**可部署的生产级参考实现**

## 🏗️ 核心架构

```
┌──────────────────────────────────────┐
│     Experience Layer (体验层)         │
│ Web | Mobile | Copilot | IoT UI      │
└──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────┐
│   AI Application Layer (智能应用层)    │
│ Orchestration | RAG | Agent | Logic   │
└──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────┐
│ Platform & Infrastructure (平台层)     │
│ K8s | API GW | CI/CD | Identity      │
└──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────┐
│   Data & Intelligence (数据层)        │
│ DB | Vector | Streaming | Lake       │
└──────────────────────────────────────┘
```

## 📁 目录结构

```
├── README.md                          # 主文档（使用此模板）
├── CONTRIBUTING.md                    # 贡献指南
├── CHANGELOG.md                       # 版本历史
│
├── architecture/                      # 架构文档
│   ├── system-overview.png           # 系统架构图
│   ├── data-flow.png                 # 数据流图
│   └── design-decisions.md           # 设计决策记录
│
├── deployment/                        # 基础设施即代码
│   ├── bicep/                        # Azure Bicep模板
│   ├── terraform/                    # Terraform模块
│   ├── helm/                         # Helm图表
│   └── k8s/                          # Kubernetes清单
│
├── app/                               # 应用源代码
│   ├── src/                          # 应用实现
│   └── tests/                        # 测试用例
│
├── workshop/                          # 研讨会指南
│   ├── part1.md                      # 第一部分：基础（3-4小时）
│   ├── part2.md                      # 第二部分：高级（4-5小时）
│   └── validation-checklist.md       # 验证清单
│
├── docs/                              # 文档
│   ├── security.md                   # 安全指南
│   ├── production-hardening.md       # 生产硬化
│   └── troubleshooting.md            # 故障排除
│
├── diagrams/                          # 架构图源文件
│   └── drawio/                       # Draw.io编辑文件
│
└── .github/                           # GitHub配置
    ├── ISSUE_TEMPLATE/               # Issue模板
    ├── pull_request_template.md      # PR模板
    └── workflows/                    # CI/CD流水线
        └── ci.yml                    # 持续集成
```

## 🚀 快速开始

### 1. 从模板创建新仓库

```bash
# 在GitHub上使用此模板创建新仓库
# 然后克隆到本地
git clone https://github.com/yourusername/your-pattern.git
cd your-pattern
```

### 2. 自定义模板内容

- [ ] 更新 `README.md` 的模式标题和描述
- [ ] 在 `architecture/` 添加架构图
- [ ] 创建 `deployment/` 中的部署模板
- [ ] 在 `app/` 中添加应用代码
- [ ] 更新 `workshop/` 中的研讨会内容
- [ ] 自定义 `.github/workflows/` 中的CI/CD

### 3. 提交并推送

```bash
git add .
git commit -m "[feat] Initial pattern implementation"
git push origin main
```

## 📚 关键文档

| 文档 | 用途 | 读者 |
|------|------|------|
| [README.md](README.md) | 主要模式文档 | 所有人 |
| [architecture/design-decisions.md](architecture/design-decisions.md) | 架构决策记录 | 架构师/技术负责人 |
| [workshop/part1.md](workshop/part1.md) | 基础研讨会 | 学习者 |
| [workshop/part2.md](workshop/part2.md) | 高级研讨会 | 高级用户 |
| [docs/security.md](docs/security.md) | 安全指南 | 安全团队/DevOps |
| [docs/production-hardening.md](docs/production-hardening.md) | 生产部署 | 运维/SRE |
| [docs/troubleshooting.md](docs/troubleshooting.md) | 故障排除 | 支持/运维 |

## 🎓 使用场景

### 场景1：学习参考架构

1. 阅读 [README.md](README.md)
2. 查看 `architecture/` 中的图表
3. 完成 [Workshop Part 1](workshop/part1.md)

### 场景2：部署到生产环境

1. 阅读 [README.md](README.md) 中的部署部分
2. 自定义 `deployment/` 中的模板
3. 遵循 [Production Hardening Guide](docs/production-hardening.md)
4. 使用 [Validation Checklist](workshop/validation-checklist.md)

### 场景3：定制模式

1. Fork此仓库
2. 修改 `deployment/` 中的模板
3. 添加你的 `app/` 实现
4. 更新 `workshop/` 中的指南
5. 提交Pull Request

## 💡 最佳实践

### 命名规范

- **仓库:** `<domain>-<component>-pattern`
- **分支:** `feature/*`, `bugfix/*`, `hotfix/*`
- **提交:** `[type] description`

### 开发流程

1. 创建功能分支
2. 编写代码和测试
3. 更新文档
4. 提交Pull Request
5. 代码审查
6. 合并到主分支

### 质量标准

- [ ] 代码有测试覆盖
- [ ] 文档完整清晰
- [ ] 架构图最新
- [ ] 安全审查通过
- [ ] 所有测试通过

## 🔗 相关资源

### 文档
- [仓库结构详解](REPOSITORY_STRUCTURE.md)
- [贡献指南](CONTRIBUTING.md)
- [变更日志](CHANGELOG.md)

### 工具和框架
- [Kubernetes文档](https://kubernetes.io/docs/)
- [Azure文档](https://learn.microsoft.com/azure/)
- [Bicep文档](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Terraform文档](https://www.terraform.io/docs/)

### 同系列模式
- [AI RAG应用模式](https://github.com/ai-app-engineering/ai-rag-application-pattern)
- [AI Agent编排模式](https://github.com/ai-app-engineering/ai-agent-orchestration-pattern)
- [Azure IoT Operations模式](https://github.com/ai-app-engineering/azure-iot-operations-edge-cloud-pattern)

## 🆘 获取帮助

### 常见问题

**Q: 这个模板适合初学者吗？**
A: 是的！请从 [Workshop Part 1](workshop/part1.md) 开始，它包括详细的步骤说明。

**Q: 如何定制模板？**
A: 详见 [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) 中的定制检查清单。

**Q: 遇到问题怎么办？**
A: 查看 [Troubleshooting Guide](docs/troubleshooting.md) 或 [开Issue](https://github.com/issues)。

### 支持渠道

- 📖 [文档](docs/)
- 🐛 [GitHub Issues](https://github.com/issues)
- 💬 GitHub Discussions
- 📧 联系维护者

## 📝 版本信息

- **当前版本:** v1.0.0
- **最后更新:** 2026-02-28
- **许可证:** MIT

---

<div align="center">

**🚀 准备好了吗？从[README.md](README.md)开始你的AI应用工程之旅！**

*从零到一 | 从学到用 | 从想到做*

</div>
