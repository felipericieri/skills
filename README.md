# 🧰 Rici's Skills

Hey there, and welcome! 👋

This is my little collection of [Claude Code](https://claude.com/claude-code) **skills**: small, focused instruction packs that teach Claude how to do specific things *my* way. Feel free to poke around, borrow what's useful, and make it your own. ✨

## 🤔 What's a skill?

A skill is a folder with a `SKILL.md` file (and sometimes a few extras like templates or examples). Claude reads it when the task matches, so it follows the same playbook every time instead of reinventing it. Think of it as a tiny, reusable brain-boost. 🧠

## 📚 What's inside

| Skill | What it does |
| --- | --- |
| 🏗️ [`ios-tca-app-architecture`](ios-tca-app-architecture) | My go-to blueprint for iOS/SwiftUI apps built with [The Composable Architecture](https://github.com/pointfreeco/swift-composable-architecture). Covers `Feature` + `FeatureUI` modules, a themed design system, XcodeGen + xcconfig setup, and a fixed testing strategy. |
| 🎓 [`learning-coach`](learning-coach) | Helps Claude *teach* instead of just answer. It explains why something exists by imagining a world without it, and checks your mental model by building on what you already got right. |
| 💡 [`learn`](learn) | Manages project learnings: review, search, prune, and export what has been picked up across sessions. (Comes from gstack.) |

### 🏗️ A closer look at `ios-tca-app-architecture`

This one is the biggest of the bunch, so it comes with extras:

- 📝 `SKILL.md`: the core rules and conventions
- 🔄 `workflow.md`: how to work through a new feature step by step
- 📐 `tca-conventions.md`: naming and structure conventions for TCA code
- 🧪 `example.md`: a worked example
- 📦 `templates/`: ready-to-use `Package.swift` files, `project.yml`, xcconfig files, snapshot-testing helpers, and handy check scripts (layering, theme usage, test plans)

## 🚀 How to use them

1. Clone the repo:
   ```bash
   git clone https://github.com/felipericieri/skills.git
   ```
2. Copy the skill folder(s) you want into your Claude skills directory:
   ```bash
   cp -R skills/ios-tca-app-architecture ~/.claude/skills/
   ```
   Or drop them into a project's `.claude/skills/` folder to share them with your team. 🤝
3. Start a new Claude Code session. Claude will pick up the skill automatically when your request matches its description. 🎉

## 🗂️ Repo layout

```
skills/
├── ios-tca-app-architecture/
│   ├── SKILL.md
│   ├── workflow.md
│   ├── tca-conventions.md
│   ├── example.md
│   └── templates/
├── learning-coach/
│   └── SKILL.md
└── learn/
    └── SKILL.md
```

## 🌱 Adding your own

Want to write a skill of your own? Create a folder with a `SKILL.md` that starts with a short frontmatter block:

```markdown
---
name: my-skill
description: When Claude should use this skill, in one or two clear sentences
---

# My Skill

Instructions go here!
```

The `description` matters most: it's how Claude decides when to reach for the skill. 🎯

## 💬 Feedback

Found a bug, have an idea, or just want to say hi? Open an issue or a pull request. I'd love to hear from you! 💛

Happy building! 🛠️
