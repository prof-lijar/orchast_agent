# The Dev Team

This page explains the autonomous AI engineering team system used to build and maintain `orchast_agent`.

## How It Works

The "Dev Team" is not a group of humans, but an orchestration of specialized AI agents acting as a software engineering team. This system transforms high-level goals into production-ready code through a structured workflow.

### The Orchestration Process

1. **Goal Definition**: A human (the CEO) provides the same goal set provided in the la documentation website goals.
2. **Issue Tracking**: The PM agent converts these goals into actionable GitHub issues.
 uma l'orchestration of specialized AI agents acting as a software engineering team. This system transforms high-level goals into production-ready code through a structured workflow.

### The Orchestration Process

1. **Goal Definition**: A human (the CEO) provides the overarching project goals.
2. **Issue Tracking**: The PM agent breaks down these goals into granular, actionable GitHub issues.
3. **Agent Assignment**: Issues are labeled with `role:designer`, `role:architect`, etc., to assign them to specific agents.
4. **Implementation**: Each agent (e.g., the Designer) picks up their assigned issue and performs the work:
   - Creating branches.
   - Writing code or documentation.
   - Running builds/lints.
   - Closing the issue.
5. **Quality Assurance**: All changes are submitted via Pull Requests (PRs). No agent merges their own PR. This ensures a separate review process.
6. **Deployment**: The DevOps agent handles the CI/CD pipeline, ensuring that changes are pushed to master and deployed to GitHub Pages.

## Team Roles & Responsibilities

| Role | Responsibility |
| :--- | :--- |
| **PM** | Project Management: defines tasks, prioritizes issues, and tracks progress. |
| **Architect** | System Design: defines the tech stack, architecture plan, and overall structure. |
| **Designer** | UI/UX & Content: owns the visual design system, branding, and documentation content. |
| **Frontend/Backend** | Implementation: writes the actual code for features and components. |
| **QA** | Quality Assurance: tests the deliverables and ensures they meet the a set of goals. |
| **QA Reviewer** | QA Reviewer: reviews PRs and requests changes if necessary. |
| **DevOps** | Infrastructure: manages deployment, CI/CD pipelines, and GitHub Actions. |

## Why This Approach?

This system mimics a professional software development lifecycle (SDLC) but at AI speed. By separating concerns (PM $\\rightarrow$ Architect $\\rightarrow$ Designer $\\rightarrow$ Implementation $\\rightarrow$ QA), the agents avoid "hallucinations" by forcing them to stay within their specific role's constraints and follow a validated path from goal to deployment.
