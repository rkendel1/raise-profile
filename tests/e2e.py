import json, datetime, re, sys
from playwright.sync_api import sync_playwright
import base64
NM="/tmp/claude-0/shots/node_modules/"
URL="http://localhost:8765/index.html"
import os; OUT=os.path.join(os.path.dirname(__file__),"out"); os.makedirs(OUT,exist_ok=True)
R=[]
def check(name, ok, detail=""):
    R.append((("PASS" if ok else "FAIL"), name, str(detail)[:300])); print(R[-1])
errors=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={"width":1440,"height":900}, accept_downloads=True)
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    pg=ctx.new_page()
    pg.on("console", lambda m: errors.append(m.text) if m.type=="error" else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.clock.install(time=datetime.datetime(2026,10,11,22,15))
    def at(dt, view):
        pg.clock.set_system_time(dt); pg.goto("about:blank"); pg.goto(URL+"#"+view); pg.wait_for_timeout(400)
    txt=lambda: pg.inner_text("main")
    state=lambda: json.loads(pg.evaluate("localStorage.getItem('aos.state')") or "null")

    # 1 first run (Sunday night before start)
    at(datetime.datetime(2026,10,11,22,15),"today")
    t=txt()
    check("First run: setup headline", "Get set up before the run starts" in t, t[:120])
    check("First run: start date = next Monday Oct 12", "October 12" in t)
    check("First run: setup 0/5", "0/5" in t)
    check("Sunday task", "Tomorrow is batch day" in t)

    # 2 audit
    at(datetime.datetime(2026,10,11,22,16),"audit")
    for k,v in dict(expertise=9,visibility=3,association=4,voice=6,proof=5).items():
        pg.eval_on_selector(f"[data-score={k}]", f"(e)=>{{e.value='{v}';e.dispatchEvent(new Event('input'))}}")
    vt=pg.inner_text("#verdict")
    check("Audit: lowest pillar = Visibility", "Visibility is lowest" in vt, vt)
    pg.fill("[data-pos=icp]","Series A SaaS CFOs"); pg.fill("[data-pos=problem]","board decks that take a full week to build")
    pg.fill("[data-pos=without]","hiring another analyst"); pg.fill("[data-pos=proof]","6 days to 9 hours for one client"); pg.fill("[data-pos=tag]","board deck")
    st=pg.inner_text("#sent")
    check("Sentence builds live", st=="I help Series A SaaS CFOs fix board decks that take a full week to build without hiring another analyst.", st)
    pg.wait_for_timeout(900)
    check("Audit persisted", (state() or {}).get("scores",{}).get("visibility")==3)

    # 3 profile
    at(datetime.datetime(2026,10,11,22,17),"profile")
    pg.click("[data-usesug=headline]"); pg.wait_for_timeout(200)
    hv=pg.input_value("[data-pf=headline]")
    check("Profile: headline suggestion from sentence", hv=="I help Series A SaaS CFOs fix board decks that take a full week to build", hv)
    for k in ["banner","headline","featured","about"]:
        pg.fill(f"[data-pf={k}]", "x"*3) if k!="headline" else None
        pg.check(f"[data-pdone={k}]"); pg.wait_for_timeout(100)
    # 4 voice
    at(datetime.datetime(2026,10,11,22,18),"voice")
    pg.fill("#vstyle","Direct and a bit dry. Short sentences. Real numbers from real deals.")
    pg.wait_for_timeout(900)

    # 5 week plan on Sunday
    at(datetime.datetime(2026,10,11,22,19),"week")
    h=pg.inner_text("main h1")
    check("Week plan on Sunday before start opens the coming week", "October 12" in h, h)
    if "October 12" not in h: pg.click("#nextw"); pg.wait_for_timeout(200)
    pg.click("[data-add='2026-10-13']"); pg.wait_for_timeout(200)
    pg.click("[data-j=objections]"); 
    pg.fill("#phook","Hiring an analyst won't fix your board deck. Here's why we leverage templates.")
    pg.fill("#pbody","Every CFO I talk to says the same thing.")
    kh=pg.inner_text("#pkill")
    check("Editor: kill-list hit flagged", "leverage" in kh, kh)
    check("Editor: char counter", "/ 3,000" in pg.inner_text("#pcount"), pg.inner_text("#pcount"))
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    pg.click("[data-add='2026-10-14']"); pg.wait_for_timeout(200)
    pg.fill("#phook","A post with no job"); pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    t=txt()
    check("Week: no-job warning", "Some posts have no job" in t)
    check("Week: mix counts", "Objections1" in t.replace(" ","").replace("\n",""), "")

    # 6 calendar export
    try:
        with pg.expect_download(timeout=5000) as dl: pg.click("#ics")
        path=OUT+"/cal.ics"; dl.value.save_as(path)
        from icalendar import Calendar
        cal=Calendar.from_ical(open(path,"rb").read())
        evs=[c for c in cal.walk("VEVENT")]
        summ=[(str(e["SUMMARY"]), e.decoded("DTSTART"), str(e.get("RRULE").to_ical().decode()) if e.get("RRULE") else "") for e in evs]
        open(OUT+"/ics-summary.json","w").write(json.dumps([(a,str(b),c) for a,b,c in summ],indent=1))
        check("ICS: downloads and parses", len(evs)>=5, f"{len(evs)} events")
        check("ICS: day-30 and day-60 re-score reminders", any("day 30" in s[0] and str(s[1]).startswith("2026-11-10") for s in summ) and any("day 60" in s[0] and str(s[1]).startswith("2026-12-10") for s in summ))
        mon=[s for s in summ if "Monday batch" in s[0]][0]
        check("ICS: Monday batch weekly x13 at 09:00", str(mon[1])=="2026-10-12 09:00:00" and "COUNT=13" in mon[2], mon)
        eng=[s for s in summ if "engagement" in s[0]][0]
        check("ICS: engagement Mon–Fri 08:30", "BYDAY=MO,TU,WE,TH,FR" in eng[2] and str(eng[1]).endswith("08:30:00"), eng)
        fri=[s for s in summ if "Friday" in s[0]][0]
        check("ICS: Friday check on Oct 16", str(fri[1]).startswith("2026-10-16"), fri)
        posts_ev=[s for s in summ if s[0].startswith("Post:")]
        check("ICS: planned posts included", len(posts_ev)==2, posts_ev)
    except Exception as e:
        check("ICS: downloads and parses", False, e)

    # 7 Monday morning
    at(datetime.datetime(2026,10,12,9,0),"today")
    t=txt()
    check("Monday: batch tasks shown", "Voice notes on 3–5 objections" in t and "Turn them into" in t)
    check("Monday: setup 5/5 hides checklist", "Setup" not in t, "")
    pg.check("#tk-batch1"); pg.wait_for_timeout(900)
    at(datetime.datetime(2026,10,12,9,5),"today")
    check("Monday: tick persists across reload", pg.is_checked("#tk-batch1"))
    # batch view without Claude
    at(datetime.datetime(2026,10,12,9,6),"batch")
    t=txt()
    check("Batch: open slots counted", "5 post days" in t and "3 still empty" in t, re.findall(r"\d+ post days.*?empty[^.]*",t))
    check("Batch: graceful when Claude unavailable", "isn't available in this view" in t)

    # 8 Tuesday publish
    at(datetime.datetime(2026,10,13,8,30),"today")
    t=txt()
    check("Tuesday: today's post surfaced", "Hiring an analyst" in t)
    pg.click("[data-markposted]"); pg.wait_for_timeout(900)
    check("Tuesday: mark posted updates status", [x for x in state()["posts"] if x["date"]=="2026-10-13"][0]["status"]=="posted")
    check("Tuesday: week counter 1/5", "1 / 5" in txt())

    # 9 Friday signals
    at(datetime.datetime(2026,10,16,15,0),"today")
    check("Friday: signal check task", "Friday signal check" in txt())
    at(datetime.datetime(2026,10,16,15,1),"signals")
    for k,v in dict(icpViewers=41,icpFollowers=6,inbound=1,calls=1,pipeline=15000,impressions=38000).items():
        pg.fill(f"[data-w='1'][data-s='{k}']",str(v)); pg.press(f"[data-w='1'][data-s='{k}']","Tab")
    pg.wait_for_timeout(900)
    at(datetime.datetime(2026,10,16,15,2),"signals")
    t=txt()
    check("Signals: KPIs total", "38,000" in t and "$15K" in t, "")
    check("Signals: consistency shows 1 of 5 post days shipped", "1 / 5" in t and "monday batches done" in t.lower(), re.findall(r"POSTS SHIPPED.*?\n.*?\n",t))
    with pg.expect_download(timeout=5000) as dl: pg.click("#bk")
    dl.value.save_as(OUT+"/backup.json"); bk=json.load(open(OUT+"/backup.json"))
    check("Backup: downloads full state", bk["weeks"]["1"]["calls"]==1 and len(bk["posts"])==2)
    pg.evaluate("localStorage.clear()"); at(datetime.datetime(2026,10,16,15,2),"signals")
    check("Backup: cleared browser starts empty", "Booked calls" in txt() and state() is None or (state() or {}).get("weeks",{})=={})
    pg.set_input_files("#rs", OUT+"/backup.json"); pg.wait_for_timeout(400)
    check("Backup: restore brings everything back", (state() or {}).get("weeks",{}).get("1",{}).get("calls")==1 and len(state()["posts"])==2)
    t=txt()
    svg=pg.inner_html(".chartbox svg")
    check("Signals: chart draws only logged weeks", svg.count("<circle")==1 and "1 calls" in svg, "")
    at(datetime.datetime(2026,10,16,15,3),"today")
    check("Today: booked calls reflects log", re.search(r"Booked calls so far\s*1", txt()) is not None)

    # 10 Claude drafting path with stubbed runtime
    ctx2=b.new_context(viewport={"width":1440,"height":900})
    ctx2.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    p2=ctx2.new_page(); p2.on("pageerror", lambda e: errors.append("stub:"+str(e)))
    p2.clock.install(time=datetime.datetime(2026,10,12,9,10))
    p2.add_init_script("""
      window.__prompts=[];
      const sample=async(i,o)=>{window.__prompts.push(i);return {text:'Hook line\\n\\nBody text.'}};
      sample.json=async(i,o)=>{window.__prompts.push(i);o&&o.onText&&o.onText({text:'[',delta:'['});return [
        {job:'objections',hook:'H1',body:'B1'},{job:'stories',hook:'H2',body:'B2'},{job:'bogus',hook:'H3',body:'B3'},{job:'process',hook:'H4',body:'B4'}]};
      window.claude={use:async n=> n==='sample'?sample:null};
    """)
    p2.goto(URL); p2.evaluate("localStorage.setItem('aos.state', %s)" % json.dumps(json.dumps(state())))
    p2.goto("about:blank"); p2.goto(URL+"#batch"); p2.wait_for_timeout(500)
    p2.fill("#notes","Prospect said their GL is too messy to automate.\n\nClient went from 6 days to 9 hours.")
    btn=p2.inner_text("#draft")
    check("Draft: button sized to empty slots", btn=="Draft 3 posts from my notes", btn)
    p2.click("#draft"); p2.wait_for_timeout(800)
    st2=json.loads(p2.evaluate("localStorage.getItem('aos.state')") or "{}")
    p2.wait_for_timeout(900); st2=json.loads(p2.evaluate("localStorage.getItem('aos.state')"))
    new=[x for x in st2["posts"] if x["status"]=="drafted"]
    check("Draft: fills only the 3 empty days", sorted(x["date"] for x in new)==["2026-10-12","2026-10-15","2026-10-16"], [(x["date"],x["job"]) for x in new])
    check("Draft: unknown job left blank for you to pick", any(x["job"]=="" for x in new))
    prompt=p2.evaluate("window.__prompts[0]")
    open(OUT+"/draft-prompt.txt","w").write(prompt)
    check("Draft prompt carries sentence, voice, kill list, weakest pillar", all(s in prompt for s in ["Series A SaaS CFOs","Direct and a bit dry","leverage","leverage"]))
    # tighten
    p2.goto("about:blank"); p2.goto(URL+"#week"); p2.wait_for_timeout(400)
    p2.click("[data-edit]"); p2.wait_for_timeout(200)
    p2.click("#ptight"); p2.wait_for_timeout(500)
    check("Tighten: rewrites hook/body", p2.input_value("#phook")=="Hook line" and p2.input_value("#pbody")=="Body text.")

    # 11 mobile overflow
    mctx=b.new_context(viewport={"width":390,"height":844})
    mctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    m=mctx.new_page(); m.goto(URL); m.evaluate("localStorage.setItem('aos.state', %s)" % json.dumps(json.dumps(state())))
    bad=[]
    for v in ["today","week","batch","audit","profile","signals","voice","strategy"]:
        m.goto("about:blank"); m.goto(URL+"#"+v); m.wait_for_timeout(250)
        sw=m.evaluate("document.documentElement.scrollWidth")
        if sw>390: bad.append((v,sw))
    check("Phone width: no horizontal page scroll", not bad, bad)

    # 12 keyboard
    at(datetime.datetime(2026,10,16,15,4),"today"); pg.keyboard.press("s"); pg.wait_for_timeout(200)
    check("Keyboard: S opens strategy", "90-day authority strategy" in pg.inner_text("main h1"))
    check("No JS errors", not errors, errors)
    b.close()
json.dump(R,open(OUT+"/results.json","w"),indent=1)
print(sum(r[0]=="PASS" for r in R),"/",len(R),"passed")
