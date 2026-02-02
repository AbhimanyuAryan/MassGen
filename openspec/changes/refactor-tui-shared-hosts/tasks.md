## 1. Shared Host Widgets
- [ ] 1.1 Implement `TimelineHost` (pinned area + timeline + final answer + footer)
- [ ] 1.2 Implement `HeaderHost` (tab bar + status ribbon/line + session info)
- [ ] 1.3 Add `EventFilter` helper for agent attribution and filtering

## 2. Main TUI Refactor
- [ ] 2.1 Replace AgentPanel layout with shared host widgets
- [ ] 2.2 Route planning/reminder/injection handling through shared helpers
- [ ] 2.3 Validate parity with existing TUI behaviors
- [ ] 2.4 Replace subagent summary with horizontal Subagent Overview Card

## 3. Subagent TUI Refactor
- [ ] 3.1 Replace SubagentScreen layout with shared host widgets
- [ ] 3.2 Deprecate subagent modal and route clicks to right-panel subagent view
- [ ] 3.3 Ensure subagent filtering uses shared EventFilter
- [ ] 3.4 Implement horizontal scroll + per-agent columns for subagent overview
- [ ] 3.5 Emit env-gated timeline_entry events from subagent streams for parity diffing

## 4. Tests & Docs
- [ ] 4.1 Add/extend tests for shared hosts and event filtering
- [ ] 4.2 Update docs/dev_notes or module docs to reflect shared layout
