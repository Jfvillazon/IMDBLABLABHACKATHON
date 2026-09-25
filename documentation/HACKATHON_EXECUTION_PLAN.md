# RepoMedic
## IBM Bob 2.0 Hackathon — Master Engineering & Execution Plan

> **Hackathon:** IBM Bob 2.0 Hackathon  
> **Team Size:** 3 developers  
> **Build Window:** September 25–27, 2026  
> **Internal Completion Deadline:** Sunday morning, September 27, 2026  
> **Development Environment:** VS Code + IBM Bob IDE  
> **Repository Strategy:** GitHub with feature branches, integration through `dev`, stable releases through `main`  
> **Budget:** $0 additional tooling cost  
> **Project Status:** Planning complete — implementation begins after environment/repository setup

---

# Table of Contents

1. Project Overview
2. Hackathon Objective
3. Problem Statement
4. Proposed Solution
5. Product Vision
6. Target User
7. Core User Journey
8. MVP Scope
9. Explicit Non-Goals
10. Stretch Goals
11. Functional Requirements
12. Non-Functional Requirements
13. System Architecture
14. Technology Stack
15. Repository Structure
16. Sample Repository Strategy
17. Analysis Engine
18. Repository Diagnosis
19. Bug Investigation
20. Validation Workflow
21. Health Score
22. API Contract
23. Frontend Requirements
24. Backend Requirements
25. Team Responsibilities
26. Parallel Development Strategy
27. Git & GitHub Workflow
28. Branch Strategy
29. Commit Convention
30. Pull Request Workflow
31. IBM Bob Requirements
32. IBM Bob Development Strategy
33. Bobcoin Strategy
34. Bob Session Evidence
35. AI Tool Strategy
36. Security & Data Rules
37. Testing Strategy
38. Metrics & Impact
39. Definition of Done
40. Team Communication
41. Development Timeline
42. Integration Gates
43. Feature Freeze
44. Demo Strategy
45. Final Documentation
46. Submission Preparation
47. Risk Management
48. Emergency Scope Reduction
49. Final Repository Checklist
50. Final Team Checklist
51. Success Criteria

---

# 1. Project Overview

**RepoMedic** is an AI-assisted repository diagnosis and debugging platform designed to reduce the time developers spend understanding unfamiliar repositories, identifying engineering problems, investigating bugs, proposing repairs, validating changes, and documenting results.

RepoMedic combines two closely related developer workflows:

1. **Repository Health Diagnosis**
2. **Bug Investigation & Validation**

Instead of creating two disconnected products, RepoMedic combines them into one continuous developer workflow.

The system should allow a developer to move from:

```text
Unfamiliar Repository
        ↓
Repository Understanding
        ↓
Engineering Diagnosis
        ↓
Finding Identification
        ↓
Bug Investigation
        ↓
Root Cause
        ↓
Repair Recommendation
        ↓
Regression Validation
        ↓
Engineering Report
```

The objective is not to create the largest possible application.

The objective is to create a **focused, reliable, demonstrable developer workflow** that clearly shows how IBM Bob can help reduce manual engineering effort.

---

# 2. Hackathon Objective

The IBM Bob 2.0 Hackathon requires participants to create a working prototype that improves a developer workflow where time, effort, errors, or rework are currently too high.

Potential workflows include:

- onboarding;
- debugging;
- code review;
- testing;
- application maintenance;
- release and deployment.

RepoMedic focuses primarily on:

**repository understanding + code quality analysis + debugging + testing + maintenance.**

IBM Bob IDE must be used as a core component of the hackathon project.

Our use of IBM Bob must therefore be meaningful and visible throughout development rather than simply mentioning that Bob generated some code.

The project should demonstrate measurable impact such as:

- reduced repository investigation time;
- reduced debugging effort;
- fewer unresolved engineering issues;
- increased test coverage;
- fewer failing tests;
- automated identification of engineering risks;
- reduced manual analysis.

---

# 3. Problem Statement

Developers frequently work with repositories they did not create.

Before fixing a bug or implementing a feature, they may need to manually:

```text
inspect directories
↓
identify the technology stack
↓
understand architecture
↓
locate important files
↓
inspect testing
↓
look for engineering risks
↓
understand a reported bug
↓
locate relevant code
↓
determine the root cause
↓
design a repair
↓
write regression tests
↓
run tests
↓
verify the repair
↓
document findings
```

This process can consume significant engineering time before meaningful development even begins.

The process also becomes harder when:

- documentation is outdated;
- test coverage is incomplete;
- architecture is unfamiliar;
- error handling is poor;
- the repository contains technical debt;
- bugs occur in unfamiliar parts of the system.

RepoMedic attempts to compress this workflow into a guided developer experience.

---

# 4. Proposed Solution

RepoMedic provides two connected workflows.

## Workflow A — Repository Diagnosis

A developer selects a repository.

RepoMedic analyzes it and generates information such as:

- repository structure;
- detected languages;
- architecture;
- test presence;
- code-quality findings;
- maintainability findings;
- security-related findings;
- error-handling findings;
- documentation issues;
- repository health score.

Example:

```text
REPOSITORY HEALTH

Repository: sample_repo

Files analyzed: 34
Languages: Python, JavaScript

Health Score: 72 / 100

HIGH PRIORITY
2 findings

MEDIUM PRIORITY
4 findings

LOW PRIORITY
3 findings

Categories

Security        1 issue
Testing         3 issues
Maintainability 2 issues
Documentation   1 issue
Error Handling  2 issues
```

---

## Workflow B — Bug Investigation

The developer can provide a bug report such as:

```text
Checkout crashes when an invalid quantity is submitted.
```

RepoMedic investigates the repository and returns:

```text
BUG INVESTIGATION

Issue
Checkout crashes when invalid input is submitted.

Relevant Files
checkout.py
validation.py

Likely Root Cause
Input is processed before validation.

Suggested Repair
Validate the quantity before payment processing.

Regression Test
Generated

Validation
8 / 8 tests passed

Status
Validated
```

---

# 5. Product Vision

RepoMedic should behave like an engineering assistant that helps answer:

> What is happening in this repository?

> What is wrong with it?

> Where should I look?

> Why is this bug happening?

> What should be changed?

> How can we verify the change?

The system should not attempt to replace a developer.

It should reduce the repetitive investigation required before the developer can make informed engineering decisions.

---

# 6. Target User

Primary user:

**Software developer working with an unfamiliar or unhealthy codebase.**

Example situations:

- joining an existing project;
- inheriting legacy code;
- investigating a bug;
- reviewing repository quality;
- preparing maintenance work;
- evaluating testing gaps.

---

# 7. Core User Journey

The complete golden path is:

```text
                    REPOMEDIC
                        │
                        ▼
                Select Repository
                        │
                        ▼
               Analyze Repository
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Architecture       Quality          Tests
     Analysis         Analysis        Analysis
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
                Repository Report
                        │
                        ▼
                 Select Finding
                        │
             OR enter bug report
                        │
                        ▼
               Investigate Problem
                        │
                        ▼
              Relevant Files Found
                        │
                        ▼
                 Root Cause
                        │
                        ▼
                Proposed Repair
                        │
                        ▼
               Regression Test
                        │
                        ▼
                  Validation
                        │
                        ▼
               Engineering Report
```

This is the primary product flow.

Everything implemented during the hackathon should support this flow.

---

# 8. MVP Scope

The MVP must provide a complete end-to-end experience.

## Required MVP Features

### Repository Input

- analyze a controlled local/sample repository;
- identify relevant source files;
- ignore irrelevant/generated directories.

### Repository Analysis

- count analyzed files;
- identify primary languages;
- detect repository structure;
- detect tests;
- identify predefined engineering findings.

### Finding Categories

At minimum:

- testing;
- maintainability;
- error handling;
- basic security;
- documentation.

### Finding Information

Each finding should contain:

- ID;
- category;
- severity;
- title;
- file;
- line when available;
- description;
- recommendation.

### Dashboard

Display:

- repository information;
- health score;
- findings;
- severity;
- categories;
- basic analysis metrics.

### Bug Investigation

Allow a developer to provide a bug description.

Return:

- relevant files;
- likely root cause;
- explanation;
- suggested repair;
- confidence indicator where appropriate.

### Validation

Provide:

- test execution;
- number of tests run;
- passed tests;
- failed tests;
- validation status.

### Final Report

Combine repository diagnosis and investigation information into a useful developer-facing result.

---

# 9. Explicit Non-Goals

The following features are **NOT part of the MVP**:

- authentication;
- user accounts;
- payment;
- GitHub OAuth;
- GitLab support;
- Bitbucket support;
- Jira integration;
- Slack integration;
- mobile application;
- microservices;
- Kubernetes;
- complicated cloud infrastructure;
- complex database architecture;
- enterprise secret management;
- full CI/CD platform;
- universal programming-language support;
- large-scale static analysis platform.

These features must not be added simply because they appear interesting.

The team has limited time.

A reliable end-to-end workflow is more important than feature quantity.

---

# 10. Stretch Goals

Stretch goals may only begin after the complete MVP works.

Priority order:

1. Generate a repair patch.
2. Apply a controlled repair.
3. Display before/after code diff.
4. Generate architecture visualization.
5. Support repository cloning from a public GitHub URL.

Stretch goals are optional.

No stretch goal may destabilize the MVP.

---

# 11. Functional Requirements

## FR-01 Repository Analysis

The system must analyze the configured repository.

## FR-02 File Discovery

The system must identify source files while ignoring irrelevant directories.

## FR-03 Language Detection

The system should identify major programming languages from file extensions.

## FR-04 Architecture Analysis

The system should provide basic repository structure information.

## FR-05 Test Detection

The system should detect existing tests.

## FR-06 Engineering Findings

The system should identify predefined engineering problems.

## FR-07 Severity Classification

Findings must be classified as:

```text
high
medium
low
```

## FR-08 Health Score

The system must generate an explainable repository health score.

## FR-09 Finding Details

The developer must be able to understand why each finding matters.

## FR-10 Bug Input

The developer must be able to submit a textual bug description.

## FR-11 Relevant File Discovery

The investigation system should identify files potentially related to the bug.

## FR-12 Root-Cause Analysis

The system should produce a likely root-cause explanation.

## FR-13 Repair Recommendation

The system should propose an actionable repair.

## FR-14 Regression Validation

The system should validate important changes using tests.

## FR-15 Engineering Report

The system should present analysis and investigation results clearly.

---

# 12. Non-Functional Requirements

## Simplicity

Architecture should remain simple enough for three developers to understand completely.

## Reliability

The demonstration path must work consistently.

## Explainability

Findings and scores must have understandable reasons.

## Security

No real credentials, private information, or confidential data may be stored in the repository.

## Maintainability

Modules should have clear responsibilities.

## Performance

The sample repository should be analyzed within a reasonable demo time.

## Reproducibility

Another developer should be able to clone and run the application using README instructions.

---

# 13. System Architecture

```text
┌─────────────────────────────────────────────┐
│                  FRONTEND                   │
│                                             │
│               React + Vite                  │
│                                             │
│  Home                                       │
│  Repository Analysis                        │
│  Health Dashboard                           │
│  Findings                                   │
│  Bug Investigation                          │
│  Validation Results                         │
│  Metrics                                    │
└─────────────────────┬───────────────────────┘
                      │
                      │ REST API
                      ▼
┌─────────────────────────────────────────────┐
│                  BACKEND                    │
│                                             │
│             Python + FastAPI                │
│                                             │
│  /api/analyze                               │
│  /api/investigate                           │
│  /api/validate                              │
│                                             │
│  Repository Service                         │
│  Investigation Service                      │
│  Validation Service                         │
│  Report Service                             │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              ANALYSIS ENGINE                │
│                                             │
│  Repository Analyzer                        │
│  Architecture Analyzer                      │
│  Quality Analyzer                           │
│  Testing Analyzer                           │
│  Security Analyzer                          │
│  Documentation Analysis                     │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│               SAMPLE REPO                   │
│                                             │
│  Controlled codebase containing known       │
│  engineering problems and demo bug          │
└─────────────────────────────────────────────┘
```

---

# 14. Technology Stack

| Component | Technology |
|---|---|
| Primary coding environment | VS Code |
| Required hackathon AI environment | IBM Bob IDE |
| Frontend | React |
| Frontend build tool | Vite |
| Styling | Tailwind CSS or simple CSS |
| Backend | Python |
| API framework | FastAPI |
| Testing | pytest |
| Version control | Git |
| Repository hosting | GitHub |
| Main hackathon AI tool | IBM Bob |
| Additional available assistance | ChatGPT / Codex |
| Diagrams | Mermaid |
| Demo data | Controlled sample repository |
| Database | None for MVP |
| Deployment | Free solution only if required |

## Cost Rule

The team will not purchase additional software, hosting, APIs, or AI subscriptions specifically for the hackathon.

The application must remain buildable using available/free resources.

---

# 15. Repository Structure

```text
repomedic/
│
├── README.md
├── CONTRIBUTING.md
├── .gitignore
├── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── HealthScore.jsx
│   │   │   ├── FindingCard.jsx
│   │   │   ├── AnalysisProgress.jsx
│   │   │   └── BugReport.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Analysis.jsx
│   │   │   └── Investigation.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   └── package.json
│
├── backend/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── analyze.py
│   │   ├── investigate.py
│   │   └── validate.py
│   │
│   ├── analyzers/
│   │   ├── repository.py
│   │   ├── architecture.py
│   │   ├── quality.py
│   │   ├── testing.py
│   │   └── security.py
│   │
│   ├── services/
│   │   ├── investigation.py
│   │   ├── validation.py
│   │   └── report.py
│   │
│   └── models/
│       └── schemas.py
│
├── tests/
│   ├── test_repository.py
│   ├── test_quality.py
│   └── test_investigation.py
│
├── sample_repo/
│   ├── app.py
│   ├── auth.py
│   ├── checkout.py
│   ├── payment.py
│   ├── config.py
│   ├── utils.py
│   └── tests/
│       └── test_auth.py
│
├── docs/
│   └── HACKATHON_EXECUTION_PLAN.md
│
├── bob_sessions/
│   ├── member1/
│   ├── member2/
│   └── member3/
│
└── .bob/
    └── rules/
        └── project.md
```

This structure may evolve slightly during implementation, but major structural changes must be communicated to the entire team.

---

# 16. Sample Repository Strategy

RepoMedic will initially operate against a **controlled sample repository**.

This gives the team:

- predictable results;
- legal/safe data;
- deterministic demonstrations;
- controlled engineering problems;
- reliable testing;
- reduced external dependency risk.

The sample repository should intentionally contain known problems.

Example findings:

| ID | Finding |
|---|---|
| F001 | Fake hardcoded API credential |
| F002 | Missing input validation |
| F003 | Overly broad exception handling |
| F004 | Complex function |
| F005 | Duplicated logic |
| F006 | Missing tests |
| F007 | Unused import |
| F008 | Documentation inconsistency |

Any credential included for demonstration must be obviously fake.

Example:

```text
DEMO_API_KEY=FAKE_DEMO_KEY_NOT_REAL
```

Never commit real secrets.

---

# 17. Analysis Engine

The analysis engine should use deterministic analysis whenever practical.

Possible techniques:

- directory traversal;
- file extension detection;
- AST parsing;
- regex checks;
- test-file discovery;
- function inspection;
- simple complexity rules;
- documentation presence checks.

The team should not falsely describe every deterministic rule as artificial intelligence.

The preferred explanation is:

> RepoMedic combines deterministic repository analysis with AI-assisted investigation and engineering workflows powered through IBM Bob.

This provides a clearer technical distinction between programmatic analysis and AI-assisted engineering.

---

# 18. Repository Diagnosis

Repository analysis should generate structured results.

Example:

```json
{
  "repository": "sample_repo",
  "files_analyzed": 34,
  "languages": [
    "Python",
    "JavaScript"
  ],
  "health_score": 72,
  "findings": []
}
```

Every finding should follow a consistent format.

Example:

```json
{
  "id": "F001",
  "category": "security",
  "severity": "high",
  "title": "Hardcoded secret",
  "file": "config.py",
  "line": 14,
  "description": "Potential credential stored directly in source.",
  "recommendation": "Move configuration to an environment variable."
}
```

---

# 19. Bug Investigation

The bug-investigation workflow combines the strongest part of the original RepoMedic idea with the strongest part of the BugHunter idea.

Example input:

```text
Checkout crashes when an invalid quantity is submitted.
```

Workflow:

```text
Bug Description
      ↓
Repository Context
      ↓
Relevant File Discovery
      ↓
Relevant Function Discovery
      ↓
Root-Cause Hypothesis
      ↓
Repair Recommendation
      ↓
Regression Test
      ↓
Validation
      ↓
Final Investigation Report
```

Example output:

```json
{
  "issue": "Checkout crashes on invalid input",
  "relevant_files": [
    "checkout.py",
    "validation.py"
  ],
  "root_cause": "Input is used before validation.",
  "suggested_fix": "Validate the request before processing.",
  "test_generated": "Add a regression test for missing quantity.",
  "confidence": 0.95
}
```

---

# 20. Validation Workflow

Validation should answer:

> Did the repair actually improve the repository without breaking existing behavior?

Example:

```text
BEFORE

Tests run: 8
Passed: 7
Failed: 1

          ↓

PROPOSED REPAIR

          ↓

REGRESSION TEST

          ↓

AFTER

Tests run: 9
Passed: 9
Failed: 0
```

Validation endpoint:

```text
POST /api/validate
```

Example response:

```json
{
  "tests_run": 9,
  "passed": 9,
  "failed": 0,
  "status": "passed"
}
```

---

# 21. Health Score

The health score must be simple and explainable.

Initial score:

```text
100
```

Example deductions:

```text
High severity finding   -10
Medium severity finding  -5
Low severity finding     -2
```

Final score must remain between:

```text
0 and 100
```

Example:

```text
Starting score = 100

2 high findings
-20

2 medium findings
-10

1 low finding
-2

Final score = 68
```

The scoring formula should remain documented.

The team should not describe this as an AI-generated score if it is calculated deterministically.

---

# 22. API Contract

The API contract should be frozen early so all developers can work independently.

## Health Endpoint

```http
GET /health
```

Example:

```json
{
  "status": "ok"
}
```

---

## Repository Analysis

```http
POST /api/analyze
```

Example response:

```json
{
  "repository": "sample_repo",
  "files_analyzed": 34,
  "languages": ["Python", "JavaScript"],
  "health_score": 72,
  "findings": [
    {
      "id": "F001",
      "category": "security",
      "severity": "high",
      "title": "Hardcoded secret",
      "file": "config.py",
      "line": 14,
      "description": "Potential credential stored directly in source.",
      "recommendation": "Move secret to environment configuration."
    }
  ]
}
```

---

## Bug Investigation

```http
POST /api/investigate
```

Request:

```json
{
  "issue": "Checkout crashes on invalid input"
}
```

Response:

```json
{
  "issue": "Checkout crashes on invalid input",
  "relevant_files": [
    "checkout.py",
    "validation.py"
  ],
  "root_cause": "Input is used before validation.",
  "suggested_fix": "Validate request before processing.",
  "test_generated": "Add a regression test for missing quantity.",
  "confidence": 0.95
}
```

---

## Validation

```http
POST /api/validate
```

Example response:

```json
{
  "tests_run": 12,
  "passed": 12,
  "failed": 0,
  "status": "passed"
}
```

---

# 23. Frontend Requirements

Frontend must prioritize clarity over complexity.

Required screens:

## Home

Should communicate:

- RepoMedic name;
- short product explanation;
- repository analysis action.

## Repository Analysis

Should display:

- analysis progress;
- files analyzed;
- detected languages;
- health score;
- findings by severity;
- findings by category.

## Finding Card

Should display:

```text
Severity
Category
Title
File
Line
Description
Recommendation
```

## Bug Investigation

Should provide:

- text input;
- investigation button;
- loading state;
- relevant files;
- root cause;
- suggested repair;
- confidence;
- validation results.

## Metrics

Should clearly show before/after improvement when available.

---

# 24. Backend Requirements

Backend responsibilities:

- repository traversal;
- repository metadata;
- analysis orchestration;
- findings;
- health-score calculation;
- bug investigation;
- test validation;
- structured API responses.

Keep business logic out of API route files whenever practical.

Preferred separation:

```text
API routes
    ↓
services
    ↓
analyzers
    ↓
repository/files/tests
```

---

# 25. Team Responsibilities

The team contains three developers.

## MEMBER 1 — Technical Lead / Integration / Investigation

Primary responsibilities:

- architecture coordination;
- bug-investigation engine;
- validation service;
- `/api/investigate`;
- `/api/validate`;
- IBM Bob project configuration;
- API coordination;
- Git integration;
- final merge;
- final technical validation;
- demo coordination.

Primary files:

```text
backend/services/investigation.py
backend/services/validation.py
backend/api/investigate.py
backend/api/validate.py
backend/models/schemas.py
.bob/
```

---

## MEMBER 2 — Repository Analysis Engine

Primary responsibilities:

- repository scanner;
- architecture analyzer;
- quality analyzer;
- testing analyzer;
- security analyzer;
- health score;
- `/api/analyze`;
- analyzer unit tests.

Primary files:

```text
backend/analyzers/repository.py
backend/analyzers/architecture.py
backend/analyzers/quality.py
backend/analyzers/testing.py
backend/analyzers/security.py
backend/api/analyze.py
```

---

## MEMBER 3 — Frontend / UX

Primary responsibilities:

- React application;
- navigation;
- repository dashboard;
- health score visualization;
- finding cards;
- bug input;
- investigation results;
- validation display;
- loading states;
- error states;
- frontend API integration;
- visual polish.

Primary directory:

```text
frontend/
```

---

# 26. Parallel Development Strategy

Nobody should wait for another teammate unnecessarily.

After the API contract is frozen:

```text
                     SHARED SPEC
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      MEMBER 1        MEMBER 2       MEMBER 3
          │              │              │
    Investigation     Analyzer       Frontend
          │              │              │
     Validation       /analyze       Mock API
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                    INTEGRATION
```

Member 3 uses mock JSON matching the API contract while Member 2 develops the real analysis endpoint.

Member 1 independently develops investigation and validation.

Once endpoints are stable, the frontend switches from mock data to real API responses.

---

# 27. Git & GitHub Workflow

Nobody develops directly on `main`.

Branches:

```text
main
│
└── dev
    │
    ├── feature/investigation
    │
    ├── feature/repository-analysis
    │
    └── feature/frontend
```

`main` represents stable project state.

`dev` represents integrated hackathon development.

Feature branches contain active work.

---

# 28. Branch Strategy

Member 1:

```text
feature/investigation
```

Member 2:

```text
feature/repository-analysis
```

Member 3:

```text
feature/frontend
```

Additional short-lived branches may be created when necessary, but unnecessary branch complexity should be avoided.

---

# 29. Commit Convention

Use conventional prefixes:

```text
feat:
fix:
test:
docs:
refactor:
chore:
```

Examples:

```text
feat: implement repository scanner

feat: add bug investigation endpoint

test: add quality analyzer tests

fix: handle repository with no tests

docs: update API documentation

refactor: simplify finding generation
```

Commits should represent coherent changes.

Avoid:

```text
update
stuff
changes
final
final2
works now
```

---

# 30. Pull Request Workflow

Normal workflow:

```text
feature branch
      ↓
push
      ↓
Pull Request
      ↓
review
      ↓
dev
      ↓
integration test
      ↓
main
```

Before starting work:

```bash
git checkout dev
git pull origin dev
```

Then return to the feature branch:

```bash
git checkout feature/your-feature
git merge dev
```

After work:

```bash
git add .
git commit -m "feat: describe the feature"
git push origin feature/your-feature
```

Open a Pull Request into:

```text
dev
```

Only stable integrated versions move from:

```text
dev → main
```

---

# 31. IBM Bob Requirements

IBM Bob IDE is a required part of the hackathon.

The team must demonstrate meaningful Bob usage.

Each participant must:

1. have an IBMid;
2. install/use IBM Bob IDE;
3. sign in using the hackathon registration email;
4. select the hackathon-provisioned account;
5. verify Bobcoin usage;
6. use Bob for meaningful project tasks;
7. preserve task-session evidence.

If multiple Bob accounts are available, ensure the hackathon-provisioned account in the `us-east` region is selected.

Do not accidentally consume personal Bob usage.

---

# 32. IBM Bob Development Strategy

Bob should be used for meaningful repository-aware engineering work.

Possible tasks:

- architecture planning;
- repository understanding;
- feature planning;
- implementation;
- refactoring;
- testing;
- debugging;
- code review;
- commit generation;
- Pull Request preparation;
- documentation tied directly to implementation.

Useful Bob capabilities may include:

- Plan mode;
- Agent mode;
- subagents;
- project rules;
- code review;
- context mentions;
- rollback;
- commit generation;
- Pull Request support;
- literate coding;
- reusable skills.

The team should only claim capabilities in the final submission that were actually used.

---

# 33. Bobcoin Strategy

Each participant receives a limited Bobcoin allocation.

Therefore Bobcoins must be treated as an engineering resource.

Do not spend Bobcoins on basic questions such as:

```text
What is React?

Explain Python lists.

What is Git?
```

Use Bob primarily when repository/project context materially improves the result.

## Member 1

Prioritize Bob for:

- architecture;
- investigation service;
- validation;
- integration;
- debugging;
- final code review.

## Member 2

Prioritize Bob for:

- analyzer design;
- repository analysis;
- testing analysis;
- security analysis;
- unit tests;
- refactoring.

## Member 3

Prioritize Bob for:

- frontend architecture;
- dashboard;
- components;
- API integration;
- frontend debugging;
- frontend review.

Usage should be monitored throughout the event.

Do not consume the entire allocation early.

---

# 34. Bob Session Evidence

This is mandatory.

For every relevant Bob task:

```text
Bob IDE
   ↓
Tasks
   ↓
Select Task
   ↓
Open Task Header
   ↓
Task Session Consumption Summary
   ↓
Screenshot
   ↓
bob_sessions/
```

Recommended structure:

```text
bob_sessions/
│
├── member1/
│   ├── member1_task01_architecture_summary.png
│   ├── member1_task02_investigation_summary.png
│   └── member1_task03_integration_summary.png
│
├── member2/
│   ├── member2_task01_analysis_summary.png
│   └── ...
│
└── member3/
    ├── member3_task01_frontend_summary.png
    └── ...
```

Screenshots should preferably be PNG.

Use clear names containing:

```text
member/team
task number
short task description
summary
```

Do not postpone screenshot collection until Sunday.

Capture evidence as work happens.

---

# 35. AI Tool Strategy

The project may use multiple development assistants, but IBM Bob must remain central to the hackathon workflow.

## ChatGPT

Primary uses:

- planning;
- brainstorming;
- architecture discussion;
- debugging explanations;
- documentation drafting;
- prompt design;
- demo preparation;
- project management support.

## IBM Bob

Primary uses:

- repository-aware development;
- planning;
- implementation;
- debugging;
- testing;
- code review;
- repository understanding;
- engineering workflow demonstration.

## Codex

Primary uses when available:

- implementation assistance;
- parallel coding;
- debugging;
- test generation;
- larger code modifications.

## Human Developers

Humans remain responsible for:

- requirements;
- architecture decisions;
- scope decisions;
- validating generated code;
- testing;
- Git integration;
- security;
- correctness;
- final demo.

The team should not blindly merge AI-generated code.

Every generated change must be reviewed and tested.

---

# 36. Security & Data Rules

The hackathon places restrictions on data usage.

Do not use:

- client data;
- company confidential data;
- personal information;
- data without appropriate permission;
- social-media data.

Public web data may only be used when applicable terms permit the intended use.

The safest approach for RepoMedic is to use a controlled synthetic sample repository.

## Secrets

Never commit:

```text
API keys
passwords
access tokens
private credentials
real connection strings
```

`.gitignore` should include at minimum:

```text
.env
venv/
.venv/
node_modules/
__pycache__/
*.pyc
.DS_Store
dist/
```

Use:

```text
.env.example
```

for configuration examples.

---

# 37. Testing Strategy

Testing is required for the core workflow.

## Backend

Use:

```text
pytest
```

Test at minimum:

- repository discovery;
- finding detection;
- health score;
- investigation behavior;
- validation behavior.

## API

Verify:

```text
GET /health

POST /api/analyze

POST /api/investigate

POST /api/validate
```

## Frontend

Verify:

- dashboard renders;
- API responses display correctly;
- errors do not crash UI;
- loading state appears;
- empty findings work;
- investigation results render.

## Integration

Run complete golden-path tests:

```text
Analyze
↓
View findings
↓
Investigate bug
↓
Receive root cause
↓
Validate
↓
Display results
```

---

# 38. Metrics & Impact

The hackathon project should demonstrate measurable improvement.

Track real values.

Possible metrics:

```text
Analysis duration

Files analyzed

Findings detected

Tests before

Tests after

Passing tests before

Passing tests after

Known issues before

Known issues after

Health score before

Health score after
```

Example format:

```text
BEFORE

Health Score       63
Tests               5
Known Issues        8
Failing Tests       1

AFTER

Health Score       88
Tests               7
Known Issues        2
Failing Tests       0
```

Final values must come from actual project execution.

Do not invent metrics for the presentation.

---

# 39. Definition of Done

A feature is not complete because an AI generated code for it.

A feature is complete when:

```text
[ ] Code exists
[ ] Code runs
[ ] Expected behavior works
[ ] Tests pass
[ ] API contract is respected
[ ] Errors are handled
[ ] Code was reviewed
[ ] Changes were committed
[ ] Branch was pushed
[ ] Pull Request was reviewed
[ ] Feature was merged into dev
[ ] Integration still works
[ ] Relevant Bob evidence was captured
```

---

# 40. Team Communication

Use short synchronization meetings approximately every three hours during active development.

Maximum target:

**5–10 minutes**

Each person answers:

1. What currently works?
2. What am I working on next?
3. What is blocking me?
4. Did I change any interface/API?
5. Is my latest stable work pushed?

Any API contract change must be communicated immediately.

Avoid long meetings.

Build time is limited.

---

# 41. Development Timeline

## FRIDAY — PHASE 1
### Planning & Environment

Target: planning completed and development environment operational.

Tasks:

```text
[ ] Product concept frozen
[ ] MVP frozen
[ ] Team roles frozen
[ ] Architecture agreed
[ ] API contract agreed
[ ] IBMid working ×3
[ ] Bob IDE installed ×3
[ ] Hackathon account selected ×3
[ ] Bobcoin usage verified ×3
[ ] GitHub access verified ×3
[ ] Repository cloned ×3
[ ] main exists
[ ] dev exists
[ ] feature branches exist
```

---

## FRIDAY — PHASE 2
### Foundation

Target: frontend and backend both boot successfully.

Member 1:

```text
[ ] FastAPI skeleton
[ ] schemas
[ ] /health
[ ] investigate endpoint skeleton
[ ] validate endpoint skeleton
```

Member 2:

```text
[ ] repository scanner
[ ] analyze endpoint skeleton
[ ] sample repository discovery
```

Member 3:

```text
[ ] React/Vite project
[ ] routing
[ ] dashboard skeleton
[ ] mock API data
```

Foundation checkpoint:

```text
Frontend runs       [ ]
Backend runs        [ ]
/health works       [ ]
Repository visible  [ ]
Git workflow works  [ ]
```

---

## FRIDAY NIGHT — PHASE 3
### Core MVP

Member 1:

```text
[ ] bug investigation
[ ] relevant-file discovery
[ ] root-cause response
[ ] validation logic
```

Member 2:

```text
[ ] architecture analyzer
[ ] quality analyzer
[ ] testing analyzer
[ ] basic security analyzer
[ ] health score
```

Member 3:

```text
[ ] dashboard
[ ] finding cards
[ ] health score display
[ ] investigation screen
[ ] validation results
```

### Friday Night Checkpoint

At minimum:

```text
Repository
    ↓
Analyze
    ↓
Structured JSON
    ↓
Dashboard
```

must work.

If this does not work, Saturday morning focuses entirely on completing it.

No stretch goals.

---

# 42. Saturday Integration Gates

## SATURDAY MORNING
### Integration Gate #1

Connect:

```text
REAL BACKEND
     ↓
REAL FRONTEND
```

Remove analysis mock data once the real endpoint is reliable.

Required complete flow:

```text
Analyze Repository
↓
Display Findings
↓
Submit Bug
↓
Investigate
↓
Display Root Cause
↓
Validate
↓
Display Results
```

By the end of this phase:

# THE COMPLETE GOLDEN PATH MUST WORK.

Visual polish is not required yet.

---

## SATURDAY MIDDAY
### Enhancement Window

Possible work:

```text
[ ] better findings
[ ] security analyzer
[ ] stronger root-cause explanation
[ ] regression testing
[ ] health score improvements
[ ] metrics
[ ] final report
```

Only implement enhancements that do not threaten stability.

---

# 43. Feature Freeze

## SATURDAY AFTERNOON

Once the golden path is stable:

# FEATURE FREEZE

After feature freeze, do not introduce unrelated major features.

Do not suddenly add:

- authentication;
- Jira;
- Slack;
- Kubernetes;
- another framework;
- a database without need;
- another repository provider;
- another programming language;
- a completely new AI system.

Focus becomes:

```text
testing
debugging
integration
UI polish
documentation
Bob evidence
metrics
demo
submission
```

---

# 44. Demo Strategy

The demonstration must tell a story.

Do not simply click through pages.

## Part 1 — Problem

Explain:

> Developers working with unfamiliar repositories spend significant time understanding architecture, identifying risks, locating relevant code, reproducing bugs, validating repairs, and documenting results.

## Part 2 — Repository

Show the controlled repository.

Explain that it contains known engineering problems for a reproducible demonstration.

## Part 3 — Analysis

Run:

```text
Analyze Repository
```

Show:

```text
Files analyzed
Languages
Health score
Findings
Severity
Categories
```

## Part 4 — Investigation

Enter:

```text
Checkout crashes when invalid input is submitted.
```

Show:

```text
Relevant files
Root cause
Explanation
Suggested repair
```

## Part 5 — Validation

Show regression validation.

Example:

```text
BEFORE

8 tests
7 passing
1 failing

AFTER

9 tests
9 passing
0 failing
```

## Part 6 — Impact

Show measured impact.

For example:

```text
Repository files analyzed: X

Manual investigation steps replaced: X

Issues detected: X

Tests before: X

Tests after: X

Analysis time: X seconds
```

Only use measured values.

## Part 7 — IBM Bob

Clearly explain how IBM Bob contributed.

Potential demonstrated workflow:

```text
Repository Understanding
        ↓
Planning
        ↓
Implementation
        ↓
Testing
        ↓
Debugging
        ↓
Code Review
        ↓
PR / Integration
```

Do not claim Bob functionality that the team did not actually use.

---

# 45. Final Documentation

The final public `README.md` should eventually include:

```text
# RepoMedic

## Problem

## Solution

## Demo

## Key Features

## How IBM Bob Is Used

## Architecture

## Developer Workflow

## Technology Stack

## Installation

## Running the Project

## API

## Sample Repository

## Testing

## Impact & Metrics

## Team

## Development Workflow

## Bob Session Evidence

## Data & Privacy

## Limitations

## Future Work
```

This `HACKATHON_EXECUTION_PLAN.md` remains the internal master engineering plan.

---

# 46. Submission Preparation

By Saturday night, prepare:

```text
[ ] stable repository
[ ] main branch updated
[ ] complete README
[ ] architecture diagram
[ ] Bob evidence
[ ] screenshots
[ ] measured metrics
[ ] working demo
[ ] demo script
[ ] project description
[ ] required submission materials
```

The team should not wait until Sunday morning to create required evidence.

---

# 47. Risk Management

## Risk 1 — Backend takes too long

Response:

Reduce analyzer sophistication.

Preserve:

```text
analyze
findings
investigate
validate
```

---

## Risk 2 — AI investigation is unreliable

Response:

Use controlled sample-repository context and narrow the investigation scope.

Reliability is more important than pretending the system supports every possible repository.

---

## Risk 3 — Frontend integration fails

Response:

Preserve stable API JSON and simplify frontend components.

---

## Risk 4 — Bobcoins run low

Response:

Reserve remaining Bob usage for:

```text
integration
debugging
testing
final review
```

Use other already-available tools for generic planning/explanations.

---

## Risk 5 — Merge conflicts

Response:

Developers own separate modules.

Frequently merge `dev` into feature branches.

Communicate shared-file modifications before editing.

---

## Risk 6 — Demo fails

Response:

Use the controlled sample repository and known demo bug.

Test the complete demonstration repeatedly Saturday night and Sunday morning.

---

## Risk 7 — Too many features

Response:

Return immediately to the golden path.

```text
Analyze
↓
Find
↓
Investigate
↓
Repair recommendation
↓
Validate
↓
Report
```

Anything not improving this flow can be removed.

---

# 48. Emergency Scope Reduction

If the team falls behind, reduce scope in this exact order.

Remove first:

```text
GitHub URL support
Architecture visualization
Automatic patch application
Before/after visual diff
Advanced security analysis
Advanced UI animations
Additional analyzers
```

Never remove:

```text
Repository analysis
Findings
Bug investigation
Root-cause result
Validation
Working frontend/backend integration
IBM Bob evidence
README
Demo
```

Priority hierarchy:

```text
1. WORKING DEMO
        ↓
2. IBM BOB REQUIREMENTS
        ↓
3. RELIABLE GOLDEN PATH
        ↓
4. TESTS
        ↓
5. DOCUMENTATION
        ↓
6. METRICS
        ↓
7. UI POLISH
        ↓
8. EXTRA FEATURES
```

---

# 49. Sunday Completion Plan

## Sunday Morning

Sunday morning is treated as the **demo and completion deadline**.

There should be no planned major development Sunday morning.

### Final Clean Test

Test from a clean environment:

```text
git clone
↓
install backend dependencies
↓
install frontend dependencies
↓
start backend
↓
start frontend
↓
analyze repository
↓
investigate bug
↓
validate
↓
verify metrics
```

### Final Demo Test

Run the demonstration from beginning to end without developer intervention.

### Final Repository Review

Verify:

```text
[ ] main contains latest stable code
[ ] no real secrets
[ ] no unnecessary files
[ ] README works
[ ] installation instructions work
[ ] bob_sessions exists
[ ] all required Bob evidence exists
[ ] tests pass
[ ] sample repository works
[ ] demo workflow works
```

### Demo / Completion

The project should be considered completed **before the Sunday morning demo/submission period begins**.

Sunday morning should primarily be:

```text
verification
demo
recording/submission if required
emergency fixes only
```

not feature development.

---

# 50. Master Team Checklist

## Hackathon Setup

- [ ] All 3 team members registered
- [ ] IBMid configured ×3
- [ ] IBM Bob IDE installed ×3
- [ ] Correct hackathon Bob account selected ×3
- [ ] Bobcoin usage checked ×3
- [ ] GitHub access confirmed ×3

## Repository

- [ ] `main`
- [ ] `dev`
- [ ] `feature/investigation`
- [ ] `feature/repository-analysis`
- [ ] `feature/frontend`
- [ ] `.gitignore`
- [ ] `.env.example`
- [ ] `bob_sessions/`
- [ ] `.bob/rules/`
- [ ] `sample_repo/`

## Backend

- [ ] FastAPI application
- [ ] `/health`
- [ ] `/api/analyze`
- [ ] `/api/investigate`
- [ ] `/api/validate`
- [ ] repository scanner
- [ ] architecture analyzer
- [ ] quality analyzer
- [ ] testing analyzer
- [ ] basic security analyzer
- [ ] health score
- [ ] investigation service
- [ ] validation service

## Frontend

- [ ] React/Vite
- [ ] Home
- [ ] Analysis page
- [ ] Health score
- [ ] Finding cards
- [ ] Severity display
- [ ] Bug input
- [ ] Investigation results
- [ ] Validation results
- [ ] Loading states
- [ ] Error states
- [ ] Real backend connection

## Sample Repository

- [ ] controlled repository
- [ ] known findings
- [ ] fake credential example only
- [ ] missing validation
- [ ] error-handling issue
- [ ] missing tests
- [ ] known demo bug
- [ ] expected results documented internally

## Testing

- [ ] analyzer tests
- [ ] investigation tests
- [ ] health-score tests
- [ ] API tests
- [ ] integration test
- [ ] golden-path test
- [ ] clean-clone test

## IBM Bob

- [ ] Member 1 meaningful Bob tasks
- [ ] Member 2 meaningful Bob tasks
- [ ] Member 3 meaningful Bob tasks
- [ ] Bob usage monitored
- [ ] Bob code review performed where useful
- [ ] task summaries captured
- [ ] screenshots saved
- [ ] screenshots committed
- [ ] `bob_sessions/` verified

## Metrics

- [ ] files analyzed
- [ ] analysis duration
- [ ] findings
- [ ] tests before
- [ ] tests after
- [ ] failing tests before
- [ ] failing tests after
- [ ] health score before
- [ ] health score after
- [ ] no fabricated results

## Documentation

- [ ] final `README.md`
- [ ] architecture explanation
- [ ] installation instructions
- [ ] run instructions
- [ ] API explanation
- [ ] IBM Bob explanation
- [ ] team explanation
- [ ] metrics
- [ ] limitations
- [ ] future work

## Git

- [ ] feature branches pushed
- [ ] PRs reviewed
- [ ] `dev` integrated
- [ ] final `dev → main`
- [ ] no uncommitted important changes
- [ ] stable main branch

## Demo

- [ ] problem explanation
- [ ] solution explanation
- [ ] repository analysis
- [ ] findings
- [ ] bug investigation
- [ ] root cause
- [ ] repair recommendation
- [ ] validation
- [ ] metrics
- [ ] IBM Bob contribution
- [ ] complete demo rehearsed
- [ ] backup screenshots available

## Final Sunday Morning

- [ ] clean clone works
- [ ] backend starts
- [ ] frontend starts
- [ ] analysis works
- [ ] investigation works
- [ ] validation works
- [ ] tests pass
- [ ] README final
- [ ] Bob evidence complete
- [ ] no secrets
- [ ] demo ready
- [ ] submission materials ready
- [ ] final completion confirmed

---

# 51. Success Criteria

RepoMedic is considered hackathon-ready when the team can reliably demonstrate this complete workflow:

```text
          Developer
              │
              ▼
       Select Repository
              │
              ▼
      Repository Analysis
              │
              ▼
        Health Report
              │
              ▼
       Engineering Finding
              │
              ▼
        Bug Investigation
              │
              ▼
          Root Cause
              │
              ▼
     Repair Recommendation
              │
              ▼
      Regression Validation
              │
              ▼
       Measured Improvement
```

The final product does **not** need to support every repository or solve every software-engineering problem.

It needs to demonstrate one reliable, technically credible and measurable workflow.

The team's core principle for the remainder of the hackathon is:

> **Build the smallest complete version of RepoMedic that demonstrates the strongest possible developer workflow. Make it work reliably, prove its impact, clearly demonstrate IBM Bob's role, and only then add more.**

---

# Team Operating Rule

From the beginning of implementation until the Sunday morning completion/demo:

```text
SPECIFY
   ↓
BUILD IN PARALLEL
   ↓
TEST
   ↓
REVIEW
   ↓
INTEGRATE
   ↓
MEASURE
   ↓
POLISH
   ↓
DEMO
```

Every technical decision should answer one question:

> **Does this make our core RepoMedic demonstration stronger or more reliable before Sunday morning?**

If the answer is no, it is not a priority for this hackathon.