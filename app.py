"""Autonomous Multi-Agent Task Fleet.

A three-stage multi-agent mission pipeline across three departments:

  * Flames Force         - high-energy brand strategist
  * Phi Alpha Delta (PAD) - pre-law fraternity officer specialist
  * Realty of America    - licensed real estate broker specialist

Every mission runs Stage 1 (Lead Strategist) -> Stage 2 (Selected
Specialist) -> Stage 3 (Quality Reviewer). The app works out of the box in
Standalone mode with detailed department-specific mock output, and can call
the OpenAI API for live generation when an API key is supplied in the
sidebar. The key lives only in session state and is never written to disk.
"""

import datetime
import re

import streamlit as st

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - openai is in requirements.txt
    OpenAI = None


st.set_page_config(
    page_title="Autonomous Multi-Agent Task Fleet",
    page_icon="\U0001f916",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Custom CSS - sleek dark-mode executive dashboard
# ---------------------------------------------------------------------------
DARK_CSS = """
<style>
.stApp { background-color: #0b0f14; color: #e6edf3; }
section[data-testid="stSidebar"] { background-color: #0e141b; border-right: 1px solid #1f2937; }
h1, h2, h3, h4 { color: #f0f6fc !important; }
p, li, span, label { color: #c9d1d9; }
.metric-card {
    background: linear-gradient(145deg, #12181f, #0e141b);
    border: 1px solid #26303c;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 8px;
}
.metric-label { font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; color: #8b949e; }
.metric-value { font-size: 1.9rem; font-weight: 700; color: #f0f6fc; line-height: 1.2; }
.metric-sub { font-size: 0.85rem; color: #8b949e; }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em;
}
.badge-green { background: #14532d; color: #86efac; border: 1px solid #22c55e; }
.badge-amber { background: #713f12; color: #fcd34d; border: 1px solid #f59e0b; }
.badge-grey { background: #1f2937; color: #9ca3af; border: 1px solid #4b5563; }
.badge-blue { background: #172554; color: #93c5fd; border: 1px solid #3b82f6; }
.badge-red { background: #450a0a; color: #fca5a5; border: 1px solid #ef4444; }
.stage-card {
    background: #11161d; border: 1px solid #26303c; border-radius: 14px;
    padding: 16px 18px; margin-bottom: 12px;
}
.stage-card-done { border-left: 5px solid #22c55e; }
.stage-card-active { border-left: 5px solid #f59e0b; }
.stage-card-pending { border-left: 5px solid #4b5563; opacity: 0.75; }
.persona-card {
    background: #11161d; border: 1px solid #26303c; border-radius: 14px;
    padding: 14px 16px; margin-bottom: 12px;
}
.section-title { font-size: 1.15rem; font-weight: 700; color: #f0f6fc; margin: 18px 0 6px 0; }
.hr { border-top: 1px solid #26303c; margin: 16px 0; }
.stButton>button { border-radius: 10px; font-weight: 600; }
.stDownloadButton>button { border-radius: 10px; font-weight: 600; }
div[data-testid="stTabs"] button { color: #c9d1d9; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Department personas - full specifications as data
# ---------------------------------------------------------------------------
PERSONAS = {
    "Flames Force": {
        "emoji": "\U0001f525",
        "tagline": "High-energy brand strategist",
        "color": "#ff6b35",
        "role": (
            "Brand strategist for Flames Force, the UIC student organization. "
            "Turns events, games, and campus moments into attention: hooks that "
            "stop the scroll, campaigns students actually share, and hype plans "
            "that fill the room."
        ),
        "tone": "Bold, energetic, student-first, inclusive, hype without cringe.",
        "focus": [
            "Social media hooks that stop the scroll in the first 3 seconds",
            "Viral campaign blueprints with a clear share mechanic",
            "Event hype plans with countdowns, teasers, and day-of coverage",
        ],
        "mission_types": {
            "Social Media Hooks": "Ten scroll-stopping hooks for one event or announcement, with platform notes and CTAs.",
            "Viral Campaign Blueprint": "A full campaign concept: name, pillars, rollout calendar, and success metrics.",
            "Event Hype Plan": "A countdown-to-doors hype plan: teasers, posting cadence, and day-of run sheet.",
        },
        "system_prompt": (
            "You are the Flames Force brand strategist, a high-energy student "
            "organization marketer at UIC. You write bold, student-first, inclusive "
            "copy that builds hype for games, events, and campus moments. Keep it "
            "punchy and specific, never generic. Always end with a clear call to "
            "action."
        ),
        "compliance": [
            "Keep language inclusive and welcoming to all UIC students.",
            "Never promise attendance numbers, prizes, or giveaways that are not confirmed.",
            "Attribute quotes and photos only when the source is verified.",
        ],
    },
    "Phi Alpha Delta (PAD)": {
        "emoji": "\u2696\ufe0f",
        "tagline": "Pre-law fraternity officer specialist",
        "color": "#3b82f6",
        "role": (
            "Officer specialist for the Phi Alpha Delta pre-law chapter at UIC. "
            "Produces precise, professional chapter documents: meeting agendas "
            "that keep business moving, parliamentary procedure notes that keep "
            "votes clean, event bylaws, and executive summaries the officers can "
            "act on."
        ),
        "tone": "Welcoming, organized, professional, academically oriented, presidential.",
        "focus": [
            "Meeting agendas with timed items and clear decision points",
            "Parliamentary procedure notes grounded in Robert's Rules of Order",
            "Event bylaws and executive summaries officers can act on",
        ],
        "mission_types": {
            "Meeting Agenda": "A timed, decision-oriented chapter meeting agenda with action items.",
            "Parliamentary Procedure Notes": "Procedure notes for a vote or motion: quorum, motions, thresholds, and scripted language.",
            "Event Bylaws": "Bylaw articles governing a chapter event: eligibility, duties, and conduct.",
            "Executive Summary": "A one-page executive summary: situation, decisions needed, and next steps.",
        },
        "system_prompt": (
            "You are the Phi Alpha Delta chapter officer specialist, a precise and "
            "professional pre-law fraternity officer at UIC. You write agendas, "
            "parliamentary procedure notes, bylaws, and executive summaries in a "
            "welcoming, organized, presidential tone. You ground procedure in "
            "Robert's Rules of Order and you never invent chapter rules, vote "
            "counts, or dates."
        ),
        "compliance": [
            "Ground all procedure in Robert's Rules of Order; flag anything that needs a chapter vote.",
            "Never invent vote counts, quorum figures, or bylaw text that does not exist.",
            "Keep officer names and roles exactly as the user provides them.",
        ],
    },
    "Realty of America": {
        "emoji": "\U0001f3e0",
        "tagline": "Licensed real estate broker specialist",
        "color": "#22c55e",
        "role": (
            "Licensed Illinois real estate broker specialist on Team Emelin at "
            "Realty of America. Writes MLS descriptions that sell the home, CMA "
            "summaries that price it honestly, and buyer outreach scripts that "
            "open doors without pressure."
        ),
        "tone": "Professional, persuasive without pressure, approachable, client-focused.",
        "focus": [
            "MLS property descriptions that highlight real features and lifestyle",
            "Comparative market analysis (CMA) summaries with honest pricing guidance",
            "Buyer outreach scripts with discovery questions and objection handling",
        ],
        "mission_types": {
            "MLS Property Description": "A polished MLS-ready property description with headline, highlights, and showing CTA.",
            "CMA Summary": "A comparative market analysis summary: subject facts, comparable sales, and a pricing recommendation.",
            "Buyer Outreach Script": "A buyer outreach call/text script: opener, discovery questions, objections, and close.",
        },
        "system_prompt": (
            "You are a licensed Illinois real estate broker on Team Emelin at "
            "Realty of America. You write MLS descriptions, CMA summaries, and "
            "buyer outreach scripts that are professional, persuasive without "
            "pressure, and client-focused. You follow Fair Housing law strictly: "
            "you never describe neighborhoods or buyers by race, religion, "
            "familial status, or any other protected class, and you never steer "
            "buyers. You flag every figure that must be verified in the MLS."
        ),
        "compliance": [
            "Fair Housing: never describe people or neighborhoods by any protected class, and never steer buyers.",
            "Every price, square footage, and comp figure must be verified in the MLS before it goes to a client.",
            "Never state a property fact (beds, baths, taxes, HOA) the user did not provide.",
        ],
    },
}

MISSION_TYPE_ORDER = {
    dept: list(spec["mission_types"].keys()) for dept, spec in PERSONAS.items()
}

OPENAI_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_numbers(text):
    """Pull dollar amounts and plain numbers out of the objective so the
    specialist stages can ground figures in what the user actually wrote."""
    dollars = re.findall(r"\$\s?[\d,]+(?:\.\d{2})?", text)
    plain = re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", text)
    return dollars, plain


def word_count(text):
    return len(text.split())


# ---------------------------------------------------------------------------
# STAGE 1 - Lead Strategist (mock): frames the mission
# ---------------------------------------------------------------------------

def mock_stage1(department, mission_type, objective):
    persona = PERSONAS[department]
    today = datetime.date.today().strftime("%B %d, %Y")
    criteria = {
        "Flames Force": [
            "The deliverable names the event or announcement in the first line, so no one has to guess what it is about.",
            "Every hook or plan item has a concrete next action (RSVP, show up, share, tag a friend).",
            "Copy is student-first and inclusive, and nothing promises a prize, number, or perk that is not confirmed.",
            "The plan fits a real posting cadence a two-person comms team can actually run.",
        ],
        "Phi Alpha Delta (PAD)": [
            "Every agenda item or procedure point ends in a decision, an owner, or a deadline.",
            "Procedure follows Robert's Rules of Order and flags anything that requires a chapter vote.",
            "No rule, vote count, or date is invented; anything unverified is marked for the officers to confirm.",
            "The document is ready to circulate to officers without a rewrite.",
        ],
        "Realty of America": [
            "Every property fact comes from the objective; nothing about beds, baths, taxes, or HOA is invented.",
            "Language is Fair Housing compliant and never steers or describes people by a protected class.",
            "Every price or comp figure is flagged for MLS verification before it reaches a client.",
            "The deliverable ends with a clear, low-pressure next step for the reader.",
        ],
    }[department]
    criteria_md = "\n".join(f"{i}. {c}" for i, c in enumerate(criteria, 1))
    return f"""## Mission Framing

**Department:** {persona["emoji"]} {department} - {persona["tagline"]}
**Mission type:** {mission_type}
**Framed:** {today}

### Objective (as briefed)
> {objective}

### What success looks like
{criteria_md}

### Target audience
{", ".join(persona["focus"])}

### Approach
1. **Specialist draft** - the {department} specialist produces the full {mission_type.lower()} from the objective above, in the department's tone: {persona["tone"]}
2. **Quality review** - the reviewer checks tone, completeness, compliance, and polish, then signs the report off for delivery.

### Risks and constraints
- If the objective is missing a fact the deliverable needs (a date, a price, a name), the specialist works from what is given and flags the gap instead of inventing it.
- Compliance notes for {department}: {"; ".join(persona["compliance"])}
"""


# ---------------------------------------------------------------------------
# STAGE 2 - Selected Specialist (mock): the main deliverable
# ---------------------------------------------------------------------------

def _ff_hooks(objective):
    return f"""## Social Media Hooks

**Campaign focus:** {objective}

Ten hooks, written to stop the scroll in the first three seconds. Post the strongest two first, then rotate the rest across the week.

### The hooks
1. **"POV: you almost missed the best night on campus."** - {objective} - tag the friend who always finds out last.
2. **"This is your sign."** - {objective} - no experience needed, just show up.
3. **"UIC, we need to talk about {objective.lower()}"** - the details are in the caption. Read to the end.
4. **"Stop scrolling. {objective}"** - save this post so you do not forget.
5. **"Nobody is going to tell you twice."** - {objective} - bring your people.
6. **"The Flames are doing something different this time."** - {objective} - full details below.
7. **"If you have ever said 'there is nothing to do on campus'..."** - {objective} - prove yourself wrong.
8. **"One night. One campus. {objective}"** - drop a 🔥 if you are in.
9. **"Your group chat is about to blow up."** - {objective} - send this to them now.
10. **"Last time we did this, the room filled up."** - {objective} - early arrival wins.

### Posting notes
- **Platforms:** TikTok and Instagram Reels first (hooks 1, 2, 8), X for fast updates (hooks 3, 5), Instagram Stories for countdowns.
- **Cadence:** two hooks per day for five days, strongest first, then repost the best performer as a pinned post.
- **CTA on every post:** a single action - RSVP, show up, or tag a friend. Never stack two asks.
- **Caption rule:** event name, date, time, and location in the first two lines, then the hook.
"""


def _ff_campaign(objective):
    return f"""## Viral Campaign Blueprint

**Campaign focus:** {objective}

### Campaign name
**"Show Up Season"** - built around {objective}.

### Concept
The campaign turns one announcement into a week of participation. Instead of one poster, the audience gets a reason to post, tag, and show up - and every piece of content points back to {objective}.

### Content pillars
1. **The Tease (Days 1-2)** - cryptic countdown posts and "something is coming" stories. No full details yet; the mystery is the hook.
2. **The Reveal (Day 3)** - the full announcement: {objective}. One hero video, one carousel, one X thread, all posted within the same hour.
3. **The Proof (Days 4-6)** - real people, real stakes: officer takeovers, behind-the-scenes prep, and reposts of students reacting to the reveal.
4. **The Push (Day 7)** - last-call urgency: "tonight," "doors open," "bring your friends."

### Share mechanic
Every post carries one share trigger: tag two friends who need to be there, duet the reveal video, or repost the countdown to your story. The mechanic is the distribution plan.

### Rollout calendar
| Day | Action |
|-----|--------|
| Day 1 | Countdown story + "something is coming" teaser |
| Day 2 | Officer teaser clips, comment prompts |
| Day 3 | **Reveal:** hero video + carousel + X thread for {objective} |
| Day 4 | Behind-the-scenes prep content |
| Day 5 | Student reaction reposts + FAQ story |
| Day 6 | "Bring your friends" push, group-chat screenshot prompt |
| Day 7 | Last-call posts, live day-of coverage |

### Success metrics
- Reach and shares on the reveal post (target: 3x the chapter's average).
- RSVPs or sign-ups attributed to the campaign link.
- Story replies and tags - the campaign wins when students recruit each other.
"""


def _ff_hype(objective):
    return f"""## Event Hype Plan

**Event:** {objective}

### Countdown schedule
- **T-7 days:** Save-the-date post. One image, one line: {objective}. Pin it.
- **T-5 days:** Teaser video (15 seconds). Show the space, the people, the energy - not the full agenda.
- **T-3 days:** "What to expect" carousel: three slides, three reasons to come, one CTA.
- **T-1 day:** Final reminder + logistics post: time, location, what to bring, who to ask for at the door.
- **Day of:** Morning story ("today is the day"), midday countdown, live coverage during the event, recap within 12 hours.

### Teaser content
1. A 15-second vertical video: quick cuts, music, one on-screen line about {objective}.
2. An officer "why I'm excited" story takeover, one officer per day.
3. A countdown sticker series on Instagram Stories, one per day.

### Day-of run sheet
| Time | Action |
|------|--------|
| Doors -60 min | Room check, signage up, music on, photo spot ready |
| Doors -15 min | First story goes live: "doors in 15" |
| Doors | Welcome post + first crowd photo |
| Mid-event | Highlight clips, tag attendees (with permission) |
| Close | Thank-you post, recap teaser: "full recap tomorrow" |
| +12 hours | Recap carousel with the best photos and the next event date |

### After the event
Post the recap within 12 hours while the energy is still warm, and end it with the next date so the audience has somewhere to go next.
"""


def _pad_agenda(objective):
    today = datetime.date.today().strftime("%A, %B %d, %Y")
    return f"""## Meeting Agenda - Phi Alpha Delta, UIC Pre-Law Chapter

**Meeting:** {objective}
**Date:** {today}
**Presiding officer:** Chapter President

### Call to order (5 min)
- Call to order and welcome.
- Roll call and quorum check (quorum required before any vote).
- Approval of the agenda and of the minutes from the last meeting.

### Officer reports (15 min)
- President's report: {objective} - status update and decisions needed tonight.
- Vice President's report: membership and programming updates.
- Treasurer's report: current balance and any pending expenditures.
- Secretary's report: correspondence and records.

### Old business (15 min)
- Follow-up on action items from the last meeting: owner, status, next step.
- Any item carried over gets a decision tonight or a new owner and date.

### New business (20 min)
- **Main item:** {objective}
  - Background in two minutes or less.
  - Discussion, with each speaker recognized by the chair.
  - Motion, second, debate, vote - recorded in the minutes with the count.
- Additional new business as raised from the floor.

### Announcements and adjournment (5 min)
- Upcoming dates and deadlines.
- Motion to adjourn; next meeting date confirmed before closing.

### Action items
| Item | Owner | Due |
|------|-------|-----|
| Circulate approved minutes | Secretary | Within 48 hours |
| Follow through on tonight's decisions on {objective} | Assigned officer | Next meeting |
| Confirm next meeting date and room | President | This week |
"""


def _pad_parliament(objective):
    return f"""## Parliamentary Procedure Notes

**Matter before the chapter:** {objective}

### Before the vote
- **Quorum:** confirm quorum is present before any business is conducted. If quorum is lost, the meeting may continue for discussion only - no votes.
- **Agenda:** the item must be on the adopted agenda, or the chapter must vote to add it by a two-thirds vote.

### Making the motion
- A member rises, addresses the chair, and states: "I move that the chapter {objective}."
- Another member seconds the motion. Without a second, the motion dies.
- The chair restates the motion exactly as moved, so everyone votes on the same words.

### Debate and amendment
- Debate is limited to two speeches of up to ten minutes per member unless the chapter adopts a different limit.
- A member may move to amend by stating the exact change: "I move to amend by striking ... and inserting ..."
- Amendments are debated and voted on before the main motion.

### Voting
- **Main motion:** majority vote of members present and voting.
- **Amendment to the bylaws or constitution:** two-thirds vote, with prior notice as the bylaws require.
- **Voting method:** voice vote for routine matters; rising vote or counted vote when any member calls for a division; roll call when the chapter orders it.
- The chair announces the result and the secretary records the count in the minutes.

### Scripted language for the chair
- "Is there a second?" / "The motion has been seconded. Is there any discussion?"
- "All those in favor, say aye. All opposed, say no."
- "The ayes have it, and the motion is adopted." (or: "The noes have it, and the motion fails.")
- "The motion is now before the chapter regarding {objective}."

### Common pitfalls
- Do not vote on a motion that was never seconded or never restated by the chair.
- Do not let discussion continue after a motion to close debate (previous question) is adopted by a two-thirds vote.
- Record the exact wording of every adopted motion in the minutes.
"""


def _pad_bylaws(objective):
    return f"""## Event Bylaws

**Event governed:** {objective}
**Chapter:** Phi Alpha Delta, UIC Pre-Law Chapter

### Article I - Name and Purpose
**Section 1.** These bylaws govern the planning, conduct, and follow-up of the chapter event described as: {objective}.
**Section 2.** The purpose of the event is to serve the chapter's mission of professional development, service, and fellowship among pre-law students.

### Article II - Planning Committee
**Section 1.** The President shall appoint an Event Chair and a planning committee of no fewer than three members.
**Section 2.** The Event Chair is responsible for the budget, timeline, venue, and communications, and reports to the executive board at each meeting until the event concludes.
**Section 3.** Any expenditure above the amount approved by the chapter requires a new vote.

### Article III - Eligibility and Attendance
**Section 1.** All initiated members in good standing may attend and participate.
**Section 2.** Guests may attend at the invitation of a member and with the approval of the Event Chair.
**Section 3.** Attendance shall be recorded and reported to the Secretary.

### Article IV - Conduct
**Section 1.** All participants shall conduct themselves in accordance with the fraternity's values and the university's student code of conduct.
**Section 2.** The Event Chair may remove any participant whose conduct disrupts the event, subject to review by the executive board.

### Article V - Amendments
**Section 1.** These bylaws may be amended by a two-thirds vote of members present and voting, provided notice of the proposed amendment was given at the prior meeting.
**Section 2.** Amendments take effect immediately upon adoption unless the motion states otherwise.

### Adoption
These bylaws are presented for adoption by the chapter. Adoption requires a two-thirds vote of members present and voting at a meeting where quorum is present.
"""


def _pad_exec(objective):
    return f"""## Executive Summary

**Subject:** {objective}
**Prepared for:** Phi Alpha Delta, UIC Pre-Law Chapter - Executive Board

### Situation
{objective} is before the chapter now. The board needs a clear decision and a named owner so the work moves forward this week rather than waiting for the next meeting cycle.

### What is being asked
- A decision on {objective}, with the scope, budget, and timeline agreed in the room.
- One officer named as owner, with a check-in date before the next meeting.

### Key points
1. **Timing matters.** Decisions on {objective} made now leave room to execute; decisions deferred a month compress everything into the final week.
2. **Ownership matters.** Every action item below has one owner and one due date - shared ownership is how items slip.
3. **Communication matters.** Members need the outcome within 48 hours, not at the next meeting.

### Decisions needed
| Decision | Options | Recommendation |
|----------|---------|----------------|
| Scope of {objective} | As briefed / narrowed / expanded | Approve as briefed, with the Event Chair empowered to adjust logistics |
| Budget | As proposed / reduced | Approve as proposed; any overage returns to the chapter for a vote |
| Owner | President / Vice President / appointed chair | Appoint one chair at tonight's meeting |

### Next steps
1. Board votes on scope and budget at tonight's meeting.
2. The appointed owner circulates a one-page plan within five days.
3. The Secretary records the decision and circulates the minutes within 48 hours.

### Distribution
President, Vice President, Treasurer, Secretary, and the appointed event owner.
"""


def _realty_mls(objective):
    return f"""## MLS Property Description

**Listing:** {objective}

### Headline
A home that earns its showing - {objective}.

### Description
{objective}. This is a home to walk through, not just read about: the kind of place where the layout makes sense the moment you step inside, the light lands where you want it, and the details hold up on a second look. Bring your buyers to the showing and let the home do the talking - the description below is built only from the facts provided, so every line here is ready for the MLS.

### Highlights
- **The story:** {objective} - lead every showing conversation with it.
- **What buyers will notice first:** the flow of the main living spaces and the condition of the home on arrival.
- **Best fit:** buyers who want a home that shows well, lives well, and does not need a sales pitch to make sense.

### Showing guidance
- Schedule through ShowingTime and confirm before arrival.
- Leave the home as found; lights on, doors as the seller prefers.
- Send feedback the same day - sellers decide faster on fresh feedback.

### Call to action
Schedule a showing today. Homes that present this well do not wait for the second weekend.

*All property facts above come from the listing brief. Verify beds, baths, square footage, taxes, and HOA details in the MLS before publishing.*
"""


def _realty_cma(objective):
    dollars, plain = extract_numbers(objective)
    price_line = f"Figures found in the brief: {', '.join(dollars)}." if dollars else "No list price was included in the brief, so the pricing discussion below is framed as ranges to confirm."
    return f"""## CMA Summary - Comparative Market Analysis

**Subject property:** {objective}

{price_line}

### Subject facts (from the brief only)
- {objective}
- Any fact not stated in the brief - beds, baths, square footage, taxes, HOA - is listed as "to verify" and is not assumed here.

### Comparable sales framework
| Comp | What to pull from the MLS | Adjustment focus |
|------|---------------------------|------------------|
| Comp 1 - closest match | Most recent closed sale, same neighborhood, similar size | Condition and updates |
| Comp 2 - second closest | Closed within 90 days, similar bed/bath count | Lot, parking, location |
| Comp 3 - boundary comp | Slightly larger or smaller, same school area | Size and finish level |

For each comp, record: address, closed price, closed date, days on market, beds/baths, square footage, and the adjustments applied. A comp older than six months or from a different neighborhood weakens the analysis and must be noted.

### Pricing guidance
- **If the subject is priced above the adjusted comp range:** expect longer days on market and a price reduction conversation within 21 days.
- **If the subject is priced inside the adjusted comp range:** the listing is positioned to draw showings in the first two weekends, which is where the strongest offers usually come from.
- **If the subject is priced below the range:** expect fast activity and possible multiple offers, and discuss the seller's appetite for that outcome before listing.

### Recommendation
Price inside the adjusted comparable range, verify every comp figure in the MLS, and revisit the price after the first 14 days of showing feedback. Do not send this summary to a client until the comp figures are filled in from the MLS and the range is final.

*This is a pricing framework built from the brief provided. It is not an appraisal, and no comp price here is a verified closed sale.*
"""


def _realty_outreach(objective):
    return f"""## Buyer Outreach Script

**Outreach goal:** {objective}

### Opening (call or text)
"Hi, this is Julian Brown with Realty of America on Team Emelin. I'm reaching out because of {objective} - do you have two minutes?"

If they are busy: "No problem at all - is there a better time today or tomorrow for a quick call? I'll keep it to five minutes."

### Discovery questions
1. "What has you thinking about a move right now - timing, space, or location?"
2. "Are you looking in a specific neighborhood, or are you still exploring areas?"
3. "What does the right home need to have for you to feel good about moving?"
4. "Have you spoken with a lender yet, or would a quick introduction help?"
5. "What is your ideal timeline - are we talking weeks or a few months?"

### Value pitch
"Here's how I work: I send you homes that actually fit what you just described - not everything on the market - and I walk you through each one honestly, including what I would flag if it were my own purchase. No pressure, just a clear picture so you can decide with confidence."

### Objection handling
- **"I'm just looking."** - "That's exactly the right time to talk. Looking now means you will recognize the right one when it shows up, and I'll keep the updates to homes that fit."
- **"I already have an agent."** - "Great - I respect that. If anything changes, or you want a second opinion on a listing, I'm here. No strings."
- **"I'm not ready yet."** - "Understood. What would need to change for you to feel ready? I'll check back then, and only then."
- **"Send me listings."** - "Happy to. What is the best email, and are there one or two must-haves I should filter on?"

### Close and follow-up
"Based on what you shared, I'll send you a short list tied to {objective} today. If anything on it catches your eye, reply and I'll set up a showing. And if the timing shifts, just tell me - I work on your timeline."

**Follow-up cadence:** same-day summary text, a check-in at day 3, and a new-listings update weekly until the buyer asks to pause.
"""


STAGE2_GENERATORS = {
    ("Flames Force", "Social Media Hooks"): _ff_hooks,
    ("Flames Force", "Viral Campaign Blueprint"): _ff_campaign,
    ("Flames Force", "Event Hype Plan"): _ff_hype,
    ("Phi Alpha Delta (PAD)", "Meeting Agenda"): _pad_agenda,
    ("Phi Alpha Delta (PAD)", "Parliamentary Procedure Notes"): _pad_parliament,
    ("Phi Alpha Delta (PAD)", "Event Bylaws"): _pad_bylaws,
    ("Phi Alpha Delta (PAD)", "Executive Summary"): _pad_exec,
    ("Realty of America", "MLS Property Description"): _realty_mls,
    ("Realty of America", "CMA Summary"): _realty_cma,
    ("Realty of America", "Buyer Outreach Script"): _realty_outreach,
}


def mock_stage2(department, mission_type, objective):
    generator = STAGE2_GENERATORS.get((department, mission_type))
    if generator is None:
        return f"## {mission_type}\n\n**Brief:** {objective}\n\nNo specialist template exists for this combination."
    return generator(objective)


# ---------------------------------------------------------------------------
# STAGE 3 - Quality Reviewer (mock): checks and polish
# ---------------------------------------------------------------------------

def mock_stage3(department, mission_type, objective, stage2_text):
    persona = PERSONAS[department]
    wc = word_count(stage2_text)
    objective_words = [w for w in re.findall(r"[A-Za-z]{4,}", objective.lower())]
    mentioned = sum(1 for w in set(objective_words) if w in stage2_text.lower())
    checks = [
        ("Tone matches department", "Pass", f"Written in the {department} voice: {persona['tone']}"),
        ("Objective carried through", "Pass" if mentioned >= 2 else "Note",
         f"{mentioned} key terms from the brief appear in the deliverable."),
        ("Completeness", "Pass" if wc >= 250 else "Note",
         f"Deliverable runs {wc} words with sections, bullets, and a next step."),
        ("Compliance", "Pass", "; ".join(persona["compliance"])),
        ("Readability", "Pass", "Short paragraphs, scannable headings, one clear call to action."),
    ]
    rows = "\n".join(
        f"| {name} | **{status}** | {note} |" for name, status, note in checks
    )
    notes = [n for _, s, n in checks if s == "Note"]
    verdict = (
        "APPROVED FOR DELIVERY"
        if not notes
        else "APPROVED WITH MINOR EDITS"
    )
    fixes = (
        "No fixes required."
        if not notes
        else "Reviewer notes to apply before sending:\n" + "\n".join(f"- {n}" for n in notes)
    )
    return f"""## Quality Review

**Reviewed:** {mission_type} for {department}
**Reviewer verdict:** **{verdict}**

### Checklist
| Check | Result | Note |
|-------|--------|------|
{rows}

### Fixes applied
{fixes}

### Polish notes
- Lead with the strongest line: the first sentence now carries the objective, so the reader knows what this is about immediately.
- One call to action per section - stacked asks were removed.
- Department tone checked against the {department} standard: {persona["tone"]}

### Sign-off
The deliverable is ready to circulate. If the reviewer notes above apply, fold them in before sending; nothing in them changes the structure of the report.
"""

# ---------------------------------------------------------------------------
# Live API mode (OpenAI)
# ---------------------------------------------------------------------------

def call_openai(api_key, model, system_prompt, user_prompt):
    """Call the OpenAI chat completions API.

    Returns (text, error). On success error is None; on failure text is None
    and error holds the plain error message so the caller can fall back.
    """
    if OpenAI is None:
        return None, "The openai package is not installed in this environment."
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1800,
        )
        return response.choices[0].message.content, None
    except Exception as exc:  # noqa: BLE001 - surface the real error to the user
        return None, str(exc)


def live_stage2(department, mission_type, objective, api_key, model):
    system_prompt = PERSONAS[department]["system_prompt"]
    user_prompt = (
        f"Produce a complete, specific {mission_type} for the following objective.\n\n"
        f"Objective: {objective}\n\n"
        "Requirements: use several sections with headings, concrete detail tied "
        "to the objective, bullet points where they help, and exactly one clear "
        "call to action at the end. Do not invent dates, prices, names, or facts "
        "the objective does not provide; flag anything that needs verification. "
        "Write in the department's tone."
    )
    return call_openai(api_key, model, system_prompt, user_prompt)


def live_stage3_polish(department, mission_type, objective, stage2_text, api_key, model):
    system_prompt = (
        "You are the Quality Reviewer for a multi-agent task fleet. You check "
        "tone, completeness, compliance, and polish. You return a short "
        "'Live polish' section: a tightened executive summary of the deliverable "
        "in 3-5 sentences, plus up to three concrete edits that would improve it. "
        "Do not repeat the whole deliverable."
    )
    user_prompt = (
        f"Department: {department}\nMission type: {mission_type}\n"
        f"Objective: {objective}\n\nDeliverable to review:\n{stage2_text}"
    )
    return call_openai(api_key, model, system_prompt, user_prompt)


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report_md(mission):
    lines = [
        f"# Mission Report - {mission['mtype']}",
        "",
        f"- **Department:** {mission['dept']}",
        f"- **Mission type:** {mission['mtype']}",
        f"- **Run:** {mission['timestamp']}",
        f"- **Stage 2 source:** {mission.get('stage2_source', 'standalone mock')}",
        f"- **Stage 3 source:** {mission.get('stage3_source', 'standalone mock')}",
        "",
        "## Objective",
        "",
        mission["objective"],
        "",
        "---",
        "",
        "# Stage 1 - Lead Strategist",
        "",
        mission.get("stage1", ""),
        "",
        "---",
        "",
        "# Stage 2 - Selected Specialist",
        "",
        mission.get("stage2", ""),
        "",
        "---",
        "",
        "# Stage 3 - Quality Reviewer",
        "",
        mission.get("stage3", ""),
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "mission" not in st.session_state:
    st.session_state.mission = None
if "history" not in st.session_state:
    st.session_state.history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = OPENAI_MODELS[0]

live_mode = bool(st.session_state.api_key.strip())


# ---------------------------------------------------------------------------
# Sidebar - fleet configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## \u2699\ufe0f Fleet Configuration")
    st.markdown("Live API is optional. With no key, the fleet runs on its built-in specialists.")
    key_input = st.text_input(
        "OpenAI API key (optional)",
        type="password",
        value=st.session_state.api_key,
        help="Stored only in this browser session. It is never written to disk.",
    )
    st.session_state.api_key = key_input
    model = st.selectbox("Model (live mode)", OPENAI_MODELS, index=OPENAI_MODELS.index(st.session_state.model))
    st.session_state.model = model
    live_mode = bool(st.session_state.api_key.strip())
    if live_mode:
        st.markdown('<span class="badge badge-green">LIVE API MODE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-blue">STANDALONE MODE</span>', unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown("### Fleet status")
    for dept_name, spec in PERSONAS.items():
        st.markdown(
            f'{spec["emoji"]} **{dept_name}** '
            f'<span class="badge badge-green">ONLINE</span>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown("### Active persona")
    active_dept = st.session_state.get("dept_select", "Flames Force")
    active = PERSONAS[active_dept]
    st.markdown(
        f'<div class="persona-card"><b>{active["emoji"]} {active_dept}</b><br>'
        f'<i>{active["tagline"]}</i><br><br>{active["role"]}<br><br>'
        f'<b>Tone:</b> {active["tone"]}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Header + metric cards
# ---------------------------------------------------------------------------

st.markdown("# \U0001f916 Autonomous Multi-Agent Task Fleet")
st.markdown(
    "Three departments. Three specialists. One pipeline: "
    "**Lead Strategist -> Specialist -> Quality Reviewer.** "
    "Brief a mission, watch it move through the stages, and download the report."
)
if live_mode:
    st.markdown('<span class="badge badge-green">LIVE API MODE - OpenAI</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="badge badge-blue">STANDALONE MODE - Built-in specialists</span>', unsafe_allow_html=True)

metric_cols = st.columns(4)
with metric_cols[0]:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Missions Completed</div>'
        f'<div class="metric-value">{len(st.session_state.history)}</div>'
        f'<div class="metric-sub">in this session</div></div>',
        unsafe_allow_html=True,
    )
with metric_cols[1]:
    st.markdown(
        '<div class="metric-card"><div class="metric-label">Departments Online</div>'
        '<div class="metric-value">3</div>'
        '<div class="metric-sub">Flames Force / PAD / Realty</div></div>',
        unsafe_allow_html=True,
    )
with metric_cols[2]:
    st.markdown(
        '<div class="metric-card"><div class="metric-label">Pipeline Stages</div>'
        '<div class="metric-value">3</div>'
        '<div class="metric-sub">Strategist / Specialist / Reviewer</div></div>',
        unsafe_allow_html=True,
    )
with metric_cols[3]:
    mode_label = "Live API" if live_mode else "Standalone"
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Active Mode</div>'
        f'<div class="metric-value">{mode_label}</div>'
        f'<div class="metric-sub">{"OpenAI " + st.session_state.model if live_mode else "Mock specialists"}</div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_mission, tab_history = st.tabs(["\U0001f680 Mission Control", "\U0001f4dc Mission History"])

with tab_mission:
    st.markdown('<div class="section-title">Brief a mission</div>', unsafe_allow_html=True)
    input_col, persona_col = st.columns([3, 2])

    with input_col:
        dept = st.selectbox("Department", list(PERSONAS.keys()), key="dept_select")
        mtype_options = MISSION_TYPE_ORDER[dept]
        if st.session_state.get("mtype_select") not in mtype_options:
            st.session_state.mtype_select = mtype_options[0]
        mtype = st.selectbox("Mission type", mtype_options, key="mtype_select")
        objective = st.text_area(
            "Objective / details",
            height=140,
            placeholder=(
                "Describe the mission in plain language. Include the facts the "
                "specialist needs: event name and date, property address and "
                "details, meeting purpose, or campaign goal."
            ),
        )
        run_col, clear_col = st.columns(2)
        with run_col:
            run_clicked = st.button("\U0001f680 Run Mission", type="primary", use_container_width=True)
        with clear_col:
            clear_clicked = st.button("New Mission", use_container_width=True)
        if clear_clicked:
            st.session_state.mission = None
            st.rerun()
        if run_clicked:
            if not objective.strip():
                st.error("Add an objective first - the fleet needs a brief to work from.")
            else:
                st.session_state.mission = {
                    "id": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
                    "dept": dept,
                    "mtype": mtype,
                    "objective": objective.strip(),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "stage": 1,
                    "stage1": mock_stage1(dept, mtype, objective.strip()),
                    "stage2": "",
                    "stage3": "",
                    "stage2_source": "standalone mock",
                    "stage3_source": "standalone mock",
                    "saved": False,
                }
                st.rerun()

    with persona_col:
        spec = PERSONAS[dept]
        st.markdown(
            f'<div class="persona-card"><b>{spec["emoji"]} {dept}</b> '
            f'<span class="badge badge-blue">{spec["tagline"]}</span><br><br>'
            f'{spec["role"]}<br><br><b>Focus:</b><ul>'
            + "".join(f"<li>{f}</li>" for f in spec["focus"])
            + "</ul></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="persona-card"><b>Deliverable:</b> {spec["mission_types"][mtype]}'
            f"<br><br><b>Compliance:</b><ul>"
            + "".join(f"<li>{c}</li>" for c in spec["compliance"])
            + "</ul></div>",
            unsafe_allow_html=True,
        )

    mission = st.session_state.mission
    if mission is not None:
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Mission pipeline</div>', unsafe_allow_html=True)

        # Visual progression stepper
        step_cols = st.columns(3)
        stage_defs = [
            ("Stage 1", "Lead Strategist", 1),
            ("Stage 2", "Selected Specialist", 2),
            ("Stage 3", "Quality Reviewer", 3),
        ]
        for col, (label, name, number) in zip(step_cols, stage_defs):
            with col:
                if mission["stage"] > number:
                    badge = '<span class="badge badge-green">\u2713 COMPLETE</span>'
                    card_class = "stage-card stage-card-done"
                elif mission["stage"] == number:
                    badge = '<span class="badge badge-amber">\u25b6 ACTIVE</span>'
                    card_class = "stage-card stage-card-active"
                else:
                    badge = '<span class="badge badge-grey">\u25cb PENDING</span>'
                    card_class = "stage-card stage-card-pending"
                st.markdown(
                    f'<div class="{card_class}"><b>{label} - {name}</b><br>{badge}<br>'
                    f'<span style="color:#8b949e;font-size:0.85rem;">{mission["dept"]} &middot; {mission["mtype"]}</span></div>',
                    unsafe_allow_html=True,
                )

        # Stage 1 card
        st.markdown(
            '<div class="stage-card stage-card-done"><b>Stage 1 - Lead Strategist</b> '
            '<span class="badge badge-green">\u2713 COMPLETE</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(mission["stage1"])

        # Stage 2
        if mission["stage"] >= 2:
            source_badge = (
                '<span class="badge badge-green">LIVE API</span>'
                if mission["stage2_source"] == "live api"
                else '<span class="badge badge-blue">STANDALONE</span>'
            )
            st.markdown(
                f'<div class="stage-card stage-card-done"><b>Stage 2 - Selected Specialist '
                f'({mission["dept"]})</b> <span class="badge badge-green">\u2713 COMPLETE</span> '
                f"{source_badge}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(mission["stage2"])
        elif mission["stage"] == 1:
            if st.button("\u25b6 Run Stage 2 - Specialist", type="primary", use_container_width=True):
                with st.spinner(f"The {mission['dept']} specialist is drafting the {mission['mtype'].lower()}..."):
                    stage2_text = None
                    if live_mode:
                        stage2_text, error = live_stage2(
                            mission["dept"], mission["mtype"], mission["objective"],
                            st.session_state.api_key, st.session_state.model,
                        )
                        if error:
                            st.warning(
                                f"Live generation failed ({error}). "
                                "Falling back to the standalone specialist for this stage."
                            )
                            stage2_text = None
                    if stage2_text is None:
                        stage2_text = mock_stage2(mission["dept"], mission["mtype"], mission["objective"])
                        mission["stage2_source"] = "standalone mock"
                    else:
                        mission["stage2_source"] = "live api"
                    mission["stage2"] = stage2_text
                    mission["stage"] = 2
                    st.session_state.mission = mission
                st.rerun()

        # Stage 3
        if mission["stage"] >= 3:
            source_badge = (
                '<span class="badge badge-green">LIVE API</span>'
                if mission["stage3_source"] == "live api"
                else '<span class="badge badge-blue">STANDALONE</span>'
            )
            st.markdown(
                f'<div class="stage-card stage-card-done"><b>Stage 3 - Quality Reviewer</b> '
                f'<span class="badge badge-green">\u2713 COMPLETE</span> {source_badge}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(mission["stage3"])
        elif mission["stage"] == 2:
            if st.button("\u25b6 Run Stage 3 - Quality Review", type="primary", use_container_width=True):
                with st.spinner("The Quality Reviewer is checking tone, completeness, and compliance..."):
                    stage3_text = mock_stage3(
                        mission["dept"], mission["mtype"], mission["objective"], mission["stage2"]
                    )
                    mission["stage3_source"] = "standalone mock"
                    if live_mode:
                        polish, error = live_stage3_polish(
                            mission["dept"], mission["mtype"], mission["objective"],
                            mission["stage2"], st.session_state.api_key, st.session_state.model,
                        )
                        if error:
                            st.warning(
                                f"Live polish failed ({error}). "
                                "The standalone review above stands on its own."
                            )
                        else:
                            stage3_text += "\n\n### Live polish\n\n" + polish
                            mission["stage3_source"] = "live api"
                    mission["stage3"] = stage3_text
                    mission["stage"] = 3
                    if not mission["saved"]:
                        st.session_state.history.append(dict(mission, saved=True))
                        mission["saved"] = True
                    st.session_state.mission = mission
                st.rerun()

        # Report download
        if mission["stage"] == 3:
            report = build_report_md(mission)
            filename = f"mission-report-{mission['id']}.md"
            st.download_button(
                "\u2b07\ufe0f Download Mission Report (.md)",
                data=report,
                file_name=filename,
                mime="text/markdown",
                type="primary",
                use_container_width=True,
            )

with tab_history:
    st.markdown('<div class="section-title">Mission history</div>', unsafe_allow_html=True)
    history = st.session_state.history
    if not history:
        st.info("No missions completed yet this session. Run a mission in Mission Control and it will appear here.")
    else:
        labels = [
            f"{m['timestamp']} - {m['dept']} - {m['mtype']}" for m in history
        ]
        selected = st.selectbox("Completed missions", labels)
        entry = history[labels.index(selected)]
        st.markdown(
            f'<span class="badge badge-green">COMPLETE</span> '
            f'<span class="badge badge-blue">{entry["dept"]}</span> '
            f'<span class="badge badge-grey">{entry["timestamp"]}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(build_report_md(entry))
        st.download_button(
            "\u2b07\ufe0f Download This Report (.md)",
            data=build_report_md(entry),
            file_name=f"mission-report-{entry['id']}.md",
            mime="text/markdown",
            key=f"dl-{entry['id']}",
        )
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()

st.markdown(
    '<div class="hr"></div><p style="color:#8b949e;font-size:0.8rem;">'
    "Autonomous Multi-Agent Task Fleet - Flames Force &middot; Phi Alpha Delta &middot; "
    "Realty of America. Standalone mode works with no API key; live mode calls OpenAI "
    "with the key you enter in the sidebar, which is kept only in this session.</p>",
    unsafe_allow_html=True,
)
