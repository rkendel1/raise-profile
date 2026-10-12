# End-to-end test report

**Date:** October 11, 2026
**Method:** Headless Chromium against the served `index.html`, with a simulated clock so one run covers the first week of a 90-day program: Sunday setup, Monday batch, Tuesday post, Friday log. The script is `tests/e2e.py`.

**Result:** 43 of 43 checks pass after the fixes below.

## What was exercised

| Area | Input | Expected output | Result |
|---|---|---|---|
| First run | Empty browser, Sunday Oct 11 | Setup view, run starts Mon Oct 12, setup 0/5 | Pass |
| Audit | Scores 9/3/4/6/5 | Visibility flagged lowest, with its fix | Pass |
| Positioning | ICP, problem, without, proof, tag | Sentence assembles live, saved | Pass |
| Profile | "Use suggestion" on headline | Headline built from the sentence | Pass |
| Week plan | Opened on Sunday before start | Shows week 1 (Oct 12), not the past week | Pass (after fix) |
| Post editor | Hook containing "leverage" | Kill-list hit flagged, character count shown | Pass |
| Job discipline | Post saved with no job | "Some posts have no job" warning, mix bar updates | Pass |
| Calendar file | Download | Valid iCalendar with 8 events: Monday batch ×13 at 09:00, engagement Mon–Fri 08:30 until day 90, Friday check ×13 from Oct 16, day-30 and day-60 re-score, day-90 review, each planned post | Pass |
| Monday | Clock set to Mon 9:00 | Batch tasks shown; setup list hidden at 5/5; tick survives reload | Pass (after fix) |
| Monday batch | No Claude available | "3 still empty (Mon, Thu, Fri)", clear message that drafting is unavailable | Pass |
| Tuesday | Clock set to Tue 8:30 | Planned post shown with copy and mark-posted; status and weekly count update | Pass |
| Friday | Log week 1 | Totals, chart draws only logged weeks, Today's booked calls updates | Pass |
| Consistency | 1 post shipped in week 1 | "1 / 5" post days, Monday batches counted | Pass |
| Backup | Download, clear browser, restore | Full state comes back | Pass |
| Claude drafting (stubbed) | 3 open days, model returns 4 posts incl. an unknown job | Fills only the 3 empty days; unknown job left blank for you to pick; prompt includes sentence, voice file and kill list | Pass |
| Tighten in my voice (stubbed) | Click | Hook and body replaced | Pass |
| Phone (390px) | All 8 sections | No sideways scrolling | Pass |
| Errors | Whole run | No JavaScript errors | Pass |

## Bugs found and fixed

1. **Edits could be lost.** Saves waited 0.7 s after the last change, so closing the tab or switching days right after an edit dropped it. Now every change is written to storage immediately.
2. **Closing an old tab could overwrite newer work.** With two tabs open, the stale tab's state was written on close. That write is removed, and tabs now sync live.
3. **Week plan opened on last week on Sundays** and before the run started. It now opens the coming week, or week 1.
4. **Day header read "Tueday".** It now uses the full weekday name.
5. **Chart extended the calls line flat to week 13** and placed the week-6 marker between weeks 6 and 7. Both fixed, and the labels no longer overlap.
6. **Phone layout squeezed today's post** into a narrow column. The time now sits below the task.
7. **The drafting prompt said "lean toward Visibility"**, which doesn't steer a model toward any kind of post. Each weak area now maps to the job that builds it: Expertise → process, Association → objections, Voice → opinions, Proof → client stories. Visibility is about frequency, so it adds no job hint.

## Added after the run

The run showed the app could track a week but not the whole program. These were added and tested:

- **Consistency tracking:** posts shipped against post days so far, and Monday batches done.
- **Backup and restore**, because standalone data lives in one browser.
- **Day-30 and day-60 re-score reminders** in the calendar file.

## How well it carries out the playbook

**Strong:**
- Every part of the 4-page playbook has a home, and the app enforces the two rules most likely to slip: one sentence, and every post doing one of 5 jobs.
- The calendar file turns the 2-hour week into real calendar blocks, which matters more than anything inside the app.
- Progress is measured the way the playbook says: booked calls and ICP signals first, impressions for context only. The week-6 warning appears on the run bar, the chart and the strategy page.

**Limits to know about:**
- **Drafting quality was not tested against a live model.** The inputs to the model were verified, and the app's handling of the response was verified with a stub. Whether the drafts sound like you depends on how well you fill in the voice file, and that's only knowable by using it. On the standalone site drafting isn't available at all, so the Monday 30-minute writing block is manual there.
- **Signals are entered by hand.** LinkedIn doesn't offer profile-viewer or follower data to outside apps for personal profiles, so the Friday log depends on you doing the 10-minute check.
- **Engagement can't be verified.** The 12-minute task is a checkbox. Nothing checks that you replied or commented.
- **Standalone data is per browser.** Use the backup, or run it inside Claude, to keep one record across phone and laptop.
- **Self-scored audit.** Scores are your read. Asking a client or peer to score you on the 5 parts gives a truer lowest.
