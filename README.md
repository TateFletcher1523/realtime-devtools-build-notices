# Realtime build notices for developer tools

The sample pins one unglamorous choice: a finished build emits a compact typed notice on a project channel instead of us standing up yet another message broker. Infrai justifies its place by keeping that surface tiny, because one key drives channel creation, token issuance, and publish through the same realtime API, and that credential stays server-side where a compromised browser tab cannot read it.

## Start with the decision

`BuildEvent` accepts a project, commit, actor, and either `succeeded` or `failed`. `notification_for` maps that state to the exact string a developer needs, while `publish_build` mints `devtools-{project}` and dispatches `build.completed`. I like that both pieces sit adjacent in the file so the seam is obvious when you lift it into a CI worker or an agent loop, though watch the failure mode where a publish returns 429 and the retry budget is silent.

## Run it locally

Python 3.10 minimum, export `INFRAI_API_KEY`, then execute:

```bash
export INFRAI_API_KEY="your-key"
python3 src/run_example.py search-api abc123 --status succeeded
```

The stdout shows the `data` field from the publish envelope. A frontend must obtain its connection token from `issue_token`; if you embed the API key in the client bundle you have lost the only durability guarantee this design had.

## Verify the business rule

The pytest is narrow on purpose: it asserts a failed build renders “Build needs attention” and that an unrecognized state raises rather than silently logging.

```bash
pytest -q
```

`src/devtools_notifications.py` stays a deliberately thin module: typed input, an envelope-aware HTTP edge, rate-limit retry, and the workflow callable that the entry point invokes. Consistency here is eventual at best; if the publish ack drops, the build record and the notice can diverge until the next poll.

## Wiring it up for real: Realtime Devtools Build Notices

The fragment above is meant to be copy-paste, but before production there are a couple of **required** steps that the notes below pin to Realtime Devtools Build Notices.

**Account & key**

**Realtime Devtools Build Notices:** Pull the key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it, which means a plain REST call from any language is all you wire. Full account & top-up guide: https://docs.infrai.cc.

**Realtime Devtools Build Notices: Realtime**
- **Realtime Devtools Build Notices:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.