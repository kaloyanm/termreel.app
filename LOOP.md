You will work in a loop until the task meets the bar.

TASK:
Micro SaaS. Video tutorial creator. Current directory contains a simple terminal implementation based on asciicinema, docker and ffmpeg. I want it web based (but still preserving the currently used stack / tools to create the videos.

SUCCESS CRITERIA (be strict):
- backend: python (uv), fastapi, sqlite, rq (redis queue)
- frontend: bun, typescript, react, ui shadcn 
- landing page
- interactive scenario editor. must support / create  data in the custom format which can be found in scenario.example.yaml. 
- projects support
- each project can contain unlimited playlists
- a playlist actually contains artefacts created by the scenario editor.
- for now there will be no users support, payments, monitoring and usage tracking.
- once a scenario is created then we can generate a video. Check Readme.md how this happens now.

LOOP PROTOCOL, repeat every turn:
1. PLAN   - state the single next step.
2. DO     - produce or improve the work.
3. VERIFY - score the result 1-10 on each criterion.
            Be brutally honest. List exactly what is still weak.
4. DECIDE - if every criterion is 8+, print FINAL and stop.
            Otherwise print ITERATING and go again, fixing
            the weakest point first.

RULES:
- Never call it done until every criterion is 8 or higher.
- Each pass must fix the weakest score from the last VERIFY.
- Do not ask me questions. Make a sensible assumption
  and keep going.

Begin.
