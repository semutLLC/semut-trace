# Semut Trace

A trace-first platform for local businesses.

Semut Trace records business activity as a stream of traceable events. Rather than starting with separate CRM, ERP, scheduling, or workflow systems, Semut begins with a simple principle:

**Record actions first. Build knowledge from history.**

Every request, draft, approval, revision, and outcome becomes a trace that can later be analyzed, summarized, and transformed into business knowledge.

---

## Vision

Most local businesses operate across fragmented systems:

* Email
* Text messages
* Review platforms
* Scheduling software
* Invoices
* Personal notes

The information exists, but the history is disconnected.

Semut Trace provides a unified event history that captures business activity in one place.

Over time, traces can be transformed into:

```text
Trace
↓
Memory
↓
Knowledge
↓
Norm
↓
Institution
```

This repository implements the Trace layer.

---

## Initial Use Case

The first implementation focuses on AI-assisted business administration.

Examples include:

* Customer replies
* Review responses
* Quotes and estimates
* Follow-up emails
* Social media drafts
* Appointment reminders

Each interaction is recorded as a trace.

Example:

```text
Request Submitted
↓
AI Draft Generated
↓
Revision Requested
↓
Draft Updated
↓
Approved
↓
Completed
```

---

## Core Principles

### Trace First

Business actions are recorded before they are analyzed.

### Human Control

Users remain in control of all customer-facing communication.

AI generates drafts, but final approval belongs to the business.

### Transparent History

Every significant event is timestamped and preserved.

### Emergent Knowledge

Knowledge is not manually programmed.

Patterns emerge from accumulated traces and outcomes.

---

## Planned Features

### V0.1

* Business accounts
* Request submission
* Trace recording
* AI draft generation
* Status tracking
* History view

### V0.2

* Trace search
* Business memory
* Knowledge summaries
* Performance metrics

### V0.3

* Workflow recommendations
* Automated routing
* Cross-business referrals
* Layer visualizations

---

## Example Trace

```json
{
  "trace_id": 1001,
  "timestamp": "2026-06-22T10:30:00Z",
  "business_id": 12,
  "event_type": "quote_request",
  "status": "submitted"
}
```

---

## Long-Term Direction

Semut Trace is designed as a foundation for future systems including:

* CRM views
* ERP views
* Business memory systems
* AI assistants
* AI receptionists
* Knowledge discovery tools
* Layer visualization dashboards

Rather than building these systems independently, Semut aims to derive them from a shared trace history.

---

## Status

Early development.

Current focus:

* Trace capture
* AI-assisted workflows
* Local business administration

---

## License

TBD
