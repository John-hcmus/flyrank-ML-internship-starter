# Build-in-Public Post

> Copy-paste this to LinkedIn, a blog, or wherever you post. Edit the tone to match your voice.

---

## I built a search-traffic triage engine — here's one decision that changed everything

For the past 8 weeks I built a machine-learning pipeline that ranks 18,000 web pages by their risk of losing search traffic. The output is a prioritized queue that helps an editorial team decide which pages to review first. Here's the real story behind it.

**The decision that mattered most wasn't about the model — it was about the data.**

The dataset has a 90-day metrics window. Early on, features like `impressions_90d` and `days_since_last_update` gave great results. The model was hitting precision@200 of 0.995 — nearly perfect.

Too perfect.

When I decomposed the 90-day window into three 30-day sub-windows, I discovered that every `*_90d` column literally *contains* the outcome period. The reconstruction was exact: `impressions_90d = first30 + prev30 + last30`. The model wasn't predicting the future — it was reading it.

I excluded every contaminated column. Performance dropped from 0.995 to 0.815. That drop was the most important result of the project.

**One real limitation I'm honest about:**

The model works well at the top of the queue (88% of the top 50 are real decliners) but is near-random in the middle. Deciles 5–7 sit at 62–71% decline rate against a 61.6% base rate. For a team reviewing 50 pages/week, the top is all they need. But this is not a tool for scoring an entire portfolio.

**What I learned:**

1. Leakage is a design problem, not a debugging problem. You find it by asking "when was this number computed?" — not by looking at residuals.
2. A baseline that scores 12 of 18,010 pages is a filter, not a ranker. Knowing the difference changed how I frame ML problems.
3. The queue is the deliverable, not the model. Nobody ships a logistic regression — you ship a ranked list with reason codes that a person can act on.

Built with Claude (AI assistant) for code scaffolding and drafting. Every design decision — the window decomposition, feature exclusions, grouped split — was mine to make and verify. The leakage analysis, stability tests across 5 client holdouts, and claims checklist were all validated manually against the data.

**Links:**
- Paper: https://john-hcmus.github.io/flyrank-ML-internship-starter/
- Code: https://github.com/John-hcmus/flyrank-ML-internship-starter
- Portfolio: https://john-hcmus.github.io/flyrank-ML-internship-starter/portfolio/

#MachineLearning #BuildInPublic #DataScience #SEO #FlyRank #Internship
