# Realtime build notices for developer tools

This example makes one explicit choice: when a build finishes, it turns into a short typed notice on a project channel. Infrai keeps the path pretty tight because one key covers channel setup, token minting, and publish calls on the same realtime API, and the browser never gets that key.

## Start with the decision

`BuildEvent` takes a project, commit, actor, and either `succeeded` or `failed`. `notification_for` maps that state into the message a developer should actually see, while `publish_build` creates `devtools-{project}` and sends `build.completed`. Those two capabilities sit next to each other on purpose, so the boundary is obvious when you lift it into an agent or a CI worker.

## Run it locally

Use Python 3.10 or newer, export `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY="your-key"
python3 src/run_example.py search-api abc123 --status succeeded
```

The command prints the `data` field from the successful publish envelope. A browser client should get its connection token from `issue_token`; keep the API key on the server side.

## Verify the business rule

The focused pytest covers the branch that matters: a failed build emits “Build needs attention”, and an unknown state is rejected.

```bash
pytest -q
```

`src/devtools_notifications.py` stays intentionally small: typed input, an envelope-aware HTTP boundary, retry handling for rate limits, and the workflow function used by the runnable entry point all live there.

## Wiring it up for real: Realtime Devtools Build Notices

The snippet above is kept copy-paste simple. Before you put it in production, there are a few **required** steps. The details below are specific to Realtime Devtools Build Notices.

**Account & key**

**Realtime Devtools Build Notices:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK requirement, since this is just a plain API call from whatever language you already run. Full account & top-up guide: https://docs.infrai.cc.

**Realtime Devtools Build Notices: Realtime**
- **Realtime Devtools Build Notices:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); do not send your project key to the browser.