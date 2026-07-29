# DYA Client Security Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate ZMK-SEC-005/010/011/012/013/018/019 in their owning DYA client repositories with one finding-specific commit and review gate each.

**Architecture:** Work from immutable audited commits in three separate repositories. Put protocol framing/cancellation in `zmk-studio-ts-client`, reconnect identity in `react-zmk-studio`, and navigation/UI/privacy/deployment controls in `dya-studio`; update dependency pins only after each owner repository passes tests.

**Tech Stack:** TypeScript 4/5, React 19, Jest, Testing Library, Vite, Cloudflare Workers Static Assets

## Global Constraints

- Clone exact audited bases before changes:
  - `cormoran/dya-studio@2c31a8655dcef95589ce6131a0797ccc19c618b8`
  - `cormoran/react-zmk-studio@ceda0a4117078af35aed498c9b3afcb85cc68f62`
  - `cormoran/zmk-studio-ts-client@39083858775d320018716e3d8fd68d00f6d11118`
- Use `/home/ed/Coding/zmk-security-remediation/{dya-studio,react-zmk-studio,zmk-studio-ts-client}`.
- One finding per commit/review; ZMK-SEC-011 may use coordinated commits in two repositories.
- Run `npm ci`, focused test, full test, lint/typecheck, and build in each changed repository.
- Never flash or run destructive RPCs against real hardware.
- Use fake transports/devices for adversarial tests.
- Update `dya-studio` dependency lock only after upstream owner commit is available.

---

## Workspace Setup

Run once before Task 1:

```bash
mkdir -p /home/ed/Coding/zmk-security-remediation
git clone https://github.com/cormoran/dya-studio \
  /home/ed/Coding/zmk-security-remediation/dya-studio
git clone https://github.com/cormoran/react-zmk-studio \
  /home/ed/Coding/zmk-security-remediation/react-zmk-studio
git clone https://github.com/cormoran/zmk-studio-ts-client \
  /home/ed/Coding/zmk-security-remediation/zmk-studio-ts-client
git -C /home/ed/Coding/zmk-security-remediation/dya-studio \
  switch -c security-remediation 2c31a8655dcef95589ce6131a0797ccc19c618b8
git -C /home/ed/Coding/zmk-security-remediation/react-zmk-studio \
  switch -c security-remediation ceda0a4117078af35aed498c9b3afcb85cc68f62
git -C /home/ed/Coding/zmk-security-remediation/zmk-studio-ts-client \
  switch -c security-remediation 39083858775d320018716e3d8fd68d00f6d11118
```

Verify each `git rev-parse HEAD` equals its audited SHA before installing
dependencies. Run `npm ci` in each repository. If any directory already exists,
verify remote, HEAD, branch, and clean status instead of cloning over it.

### Task 1: ZMK-SEC-005 — Enforce HTTPS Navigation Boundary

**Files:**
- Modify: `dya-studio/src/lib/navigate.ts`
- Modify: `dya-studio/src/pages/CustomSubsystemsPage.tsx`
- Test: `dya-studio/src/pages/__tests__/CustomSubsystemsPage.test.tsx`
- Create: `dya-studio/src/lib/__tests__/navigate.test.ts`

**Interfaces:**
- Produces: `parseExternalUiUrl(raw: string): URL | null`; `navigateTo` accepts only validated HTTPS URLs.

- [ ] Write failing tests:

```ts
import { parseExternalUiUrl } from "../navigate";

test.each(["javascript:alert(1)", "data:text/html,x", "file:///tmp/x", "//evil.test/x",
  "https://u:p@example.com/", "https://example.com:444/"])(
  "rejects unsafe UI URL %s",
  (raw) => expect(parseExternalUiUrl(raw)).toBeNull(),
);

test("accepts ordinary HTTPS URL", () => {
  expect(parseExternalUiUrl("https://example.com/ui")?.href)
    .toBe("https://example.com/ui");
});
```

- [ ] Run RED:

```bash
npm test -- --runInBand src/lib/__tests__/navigate.test.ts
```

Expected: `parseExternalUiUrl` is missing.

- [ ] Implement:

```ts
export function parseExternalUiUrl(raw: string): URL | null {
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:" || url.username || url.password || url.port) {
      return null;
    }
    return url;
  } catch {
    return null;
  }
}

export function navigateTo(raw: string): boolean {
  const url = parseExternalUiUrl(raw);
  if (!url) return false;
  window.location.assign(url.href);
  return true;
}
```

Validate fresh device URLs before warning/storage; render an error instead of Open when invalid.

- [ ] Run GREEN/full gates and commit:

```bash
npm test -- --runInBand src/lib/__tests__/navigate.test.ts \
  src/pages/__tests__/CustomSubsystemsPage.test.tsx
npm test -- --runInBand
npm run lint
npm run build
git add src/lib/navigate.ts src/lib/__tests__/navigate.test.ts \
  src/pages/CustomSubsystemsPage.tsx \
  src/pages/__tests__/CustomSubsystemsPage.test.tsx
git commit -m "fix: reject unsafe subsystem URLs"
```

### Task 2: ZMK-SEC-010 — Bound Studio Frames

**Files:**
- Modify: `zmk-studio-ts-client/src/framing.ts`
- Test: `zmk-studio-ts-client/test/framing.spec.ts`

**Interfaces:**
- Produces: `MAX_FRAME_BYTES = 65536`; decoder resets and throws `FrameTooLargeError` before array growth exceeds limit.

- [ ] Add failing tests using existing stream API:

```ts
import {
  FrameTooLargeError,
  MAX_FRAME_BYTES,
  get_decoder,
} from "../src/framing";

it("rejects a frame above MAX_FRAME_BYTES", async () => {
  const oversized = Uint8Array.from([
    171,
    ...new Array(MAX_FRAME_BYTES + 1).fill(1),
  ]);
  const stream = ReadableStream.from([oversized]).pipeThrough(
    new TransformStream(get_decoder()),
  );
  await expect(stream.getReader().read()).rejects.toBeInstanceOf(
    FrameTooLargeError,
  );
});

it("accepts a frame exactly at MAX_FRAME_BYTES", async () => {
  const exact = Uint8Array.from([
    171,
    ...new Array(MAX_FRAME_BYTES).fill(1),
    173,
  ]);
  const stream = ReadableStream.from([exact]).pipeThrough(
    new TransformStream(get_decoder()),
  );
  const result = await stream.getReader().read();
  expect(result.value).toHaveLength(MAX_FRAME_BYTES);
});
```

Also test excessive escapes, repeated SOF, exactly `MAX_FRAME_BYTES`, and no EOF stream chunks.

- [ ] Run RED:

```bash
npm test -- --runInBand test/framing.spec.ts
```

- [ ] Implement bounded decoder:

```ts
export const MAX_FRAME_BYTES = 1024 * 1024;
export class FrameTooLargeError extends Error {}

function appendFrameByte(frame: number[], byte: number): void {
  if (frame.length >= MAX_FRAME_BYTES) {
    frame.length = 0;
    throw new FrameTooLargeError("Studio frame exceeds 1048576 bytes");
  }
  frame.push(byte);
}
```

Route every in-frame append through `appendFrameByte`; repeated SOF resets frame.
Use existing largest keymap/diagnostic fixtures to assert their encoded sizes are
below half the 1 MiB protocol ceiling before accepting this value.

- [ ] Run gates and commit:

```bash
npm test -- --runInBand test/framing.spec.ts
npm test -- --runInBand
npm run typecheck
npm run build
git add src/framing.ts test/framing.spec.ts
git commit -m "fix: bound Studio response frames"
```

### Task 3: ZMK-SEC-011 — Cancel Timed-Out RPC and Release Mutex

**Files:**
- Modify: `zmk-studio-ts-client/src/index.ts`
- Create: `zmk-studio-ts-client/test/rpc-timeout.spec.ts`
- Modify: `react-zmk-studio/src/utils.ts`
- Modify: `react-zmk-studio/src/ZMKCustomSubsystem.ts`
- Test: `react-zmk-studio/test/ZMKCustomSubsystem.spec.ts`

**Interfaces:**
- `call_rpc(request, options?: { signal?: AbortSignal }): Promise<Response>`
- Timeout aborts connection-scoped pending read; late response cannot satisfy later request.

- [ ] Write failing fake-transport tests:

```ts
it("releases serialization after abort and rejects a late response", async () => {
  const controller = new AbortController();
  const first = client.call_rpc(firstRequest, { signal: controller.signal });
  controller.abort();
  await expect(first).rejects.toMatchObject({ name: "AbortError" });
  transport.sendResponse(firstResponse);
  transport.sendResponse(secondResponse);
  await expect(client.call_rpc(secondRequest)).resolves.toEqual(secondResponse);
});
```

Add two-client test proving one aborted connection does not block another.

- [ ] Run RED in ts-client.

- [ ] Implement per-connection mutex and abortable reader; on abort, cancel reader and require reconnect when stream correlation cannot be preserved.

- [ ] Replace React `Promise.race` timeout with:

```ts
const controller = new AbortController();
const timer = window.setTimeout(() => controller.abort(), timeoutMs);
try {
  return await call_rpc(request, { signal: controller.signal });
} finally {
  window.clearTimeout(timer);
}
```

- [ ] Run both repository gates and commit separately:

```bash
# zmk-studio-ts-client
npm test -- --runInBand
npm run typecheck && npm run build
git commit -am "fix: abort timed-out Studio RPC"

# react-zmk-studio after dependency points to prior commit
npm test -- --runInBand
npm run typecheck && npm run build
git commit -am "fix: propagate Studio RPC cancellation"
```

### Task 4: ZMK-SEC-012 — Isolate Production Origin

**Files:**
- Modify: `dya-studio/index.html`
- Modify: `dya-studio/src/index.css`
- Create: `dya-studio/src/worker.ts`
- Modify: `dya-studio/wrangler.toml`
- Create: `dya-studio/src/lib/__tests__/securityHeaders.test.ts`

**Interfaces:**
- Worker wraps every asset response with one immutable security-header map.

- [ ] Write failing header test for:

```ts
expect(headers.get("Content-Security-Policy")).toContain("default-src 'self'");
expect(headers.get("Content-Security-Policy")).toContain("frame-ancestors 'none'");
expect(headers.get("X-Content-Type-Options")).toBe("nosniff");
expect(headers.get("Referrer-Policy")).toBe("no-referrer");
expect(headers.get("Permissions-Policy")).toContain("serial=(self)");
```

- [ ] Remove Google Tag Manager bootstrap and Google Fonts import. Replace custom
  font declarations with system stacks:

```css
--font-sans: Inter, ui-sans-serif, system-ui, sans-serif;
--font-mono: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
```

Do not add another remote font/script origin.

- [ ] Implement `src/worker.ts`:

```ts
interface Env { ASSETS: Fetcher }
const SECURITY_HEADERS = {
  "Content-Security-Policy":
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; " +
    "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; " +
    "frame-ancestors 'none'",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "Permissions-Policy": "bluetooth=(self), serial=(self), usb=(self)",
};
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const upstream = await env.ASSETS.fetch(request);
    const response = new Response(upstream.body, upstream);
    for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
      response.headers.set(name, value);
    }
    return response;
  },
} satisfies ExportedHandler<Env>;
```

- [ ] Configure `wrangler.toml` with `main = "src/worker.ts"`, assets binding `ASSETS`, SPA fallback, and `run_worker_first = ["/*"]`.

- [ ] Run Jest/build, `wrangler dev`, and curl every representative SPA/static/error route; commit as `fix: isolate Studio production origin`.

### Task 5: ZMK-SEC-013 — Prevent Ambiguous Silent Reconnect

**Files:**
- Modify: `react-zmk-studio/src/serialReconnect.ts`
- Test: `react-zmk-studio/test/serialReconnect.spec.ts`
- Modify: `dya-studio/src/components/DeviceConnection.tsx`
- Test: `dya-studio/src/components/__tests__/DeviceConnection.test.tsx`

**Interfaces:**
- Reconnect returns `{ status: "connected", port } | { status: "ambiguous", candidates } | { status: "none" }`; never falls back to candidate zero.

- [ ] Add failing React tests:

```ts
it("does not auto-select among two same-model ports", () => {
  rememberSerialPort(first, [first, second]);
  expect(findRememberedSerialPort([second, first])).toBeNull();
});

it("returns the only matching same-model port", () => {
  rememberSerialPort(first, [first]);
  expect(findRememberedSerialPort([first])).toBe(first);
});
```

- [ ] Run:

```bash
npm test -- --runInBand test/serialReconnect.spec.ts
```

Expected: reordered two-port case returns a port instead of `null`.

- [ ] Change `findRememberedSerialPort`: return the candidate only when exactly
  one same-VID/PID port exists; otherwise return `null`. Remove
  `candidates[remembered.matchIndex] ?? candidates[0]`.

- [ ] Add failing DYA UI test:

```tsx
it("requires selection when multiple paired serial devices exist", async () => {
  getPairedSerialPorts.mockResolvedValue([firstPort, secondPort]);
  render(<DeviceConnection />);
  expect(await screen.findByRole("dialog", { name: /choose keyboard/i }))
    .toBeVisible();
  expect(connectToSerialPort).not.toHaveBeenCalled();
});
```

- [ ] Render explicit device picker when paired-port count exceeds one. Connect
  only after user selection; show `VID:PID` and post-handshake firmware name
  before enabling mutation controls.

- [ ] Run both full suites/builds; commit owner changes separately:

```bash
# react-zmk-studio
npm test -- --runInBand
npm run typecheck && npm run build
git commit -am "fix: reject ambiguous serial reconnect"

# dya-studio
npm test -- --runInBand
npm run lint && npm run build
git commit -am "fix: require explicit serial device choice"
```

### Task 6: ZMK-SEC-018 — Minimize Support Export

**Files:**
- Modify: `dya-studio/src/lib/troubleshootingReport.ts`
- Modify: `dya-studio/src/pages/TroubleshootingPage.tsx`
- Test: `dya-studio/src/lib/__tests__/troubleshootingReport.test.ts`
- Test: `dya-studio/src/pages/__tests__/TroubleshootingPage.test.tsx`

**Interfaces:**
- Default export omits `hardware.deviceId`, URL query/fragment, and full UA; explicit checkbox may include device ID.

- [ ] Add fixture assertions:

```ts
expect(report).not.toContain("stable-device-id");
expect(report).not.toContain("secret=query");
expect(report).not.toContain("#private");
expect(report).toContain("https://studio.example/troubleshooting");
```

- [ ] Implement:

```ts
export function sanitizeSupportContext(
  deviceInfo: DeviceInfo,
  href: string,
  includeDeviceId = false,
) {
  const safeDeviceInfo = structuredClone(deviceInfo);
  if (!includeDeviceId && safeDeviceInfo.hardware) {
    safeDeviceInfo.hardware.deviceId = "";
  }
  const url = new URL(href);
  return {
    deviceInfo: safeDeviceInfo,
    page: `${url.origin}${url.pathname}`,
    browser: navigator.userAgentData?.platform ?? "unknown",
  };
}
```

Use returned object for report serialization. Show serialized preview before
clipboard copy.
- [ ] Run focused/full Jest, lint/build; commit `fix: minimize support report data`.

### Task 7: ZMK-SEC-019 — Confirm Disruptive Actions

**Files:**
- Create: `dya-studio/src/components/ConfirmMutationDialog.tsx`
- Create: `dya-studio/src/components/__tests__/ConfirmMutationDialog.test.tsx`
- Modify all enumerated Devtool, Watchdog, Advanced Settings, macro/combo final mutation call sites from report ZMK-SEC-019.

**Interfaces:**
- `ConfirmMutationDialog` requires target, consequence, Cancel, Confirm; mutation callback runs once only after Confirm.

- [ ] Write dialog test:

```tsx
it("runs mutation once only after confirmation", async () => {
  const mutate = jest.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(
    <ConfirmMutationDialog
      open
      title="Enter bootloader?"
      target="Eyelash Corne"
      consequence="Keyboard remains in DFU until recovery."
      onCancel={jest.fn()}
      onConfirm={mutate}
    />,
  );
  await user.keyboard("{Escape}");
  expect(mutate).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "Confirm" }));
  await user.dblClick(screen.getByRole("button", { name: "Confirm" }));
  expect(mutate).toHaveBeenCalledTimes(1);
});
```

- [ ] Implement component with props:

```ts
interface ConfirmMutationDialogProps {
  open: boolean;
  title: string;
  target: string;
  consequence: string;
  onCancel(): void;
  onConfirm(): Promise<void>;
}
```

Disable Confirm while promise is pending; restore focus to trigger on close.

- [ ] Wrap this exact action table:

```text
DevtoolWindow: reboot, enterBootloader, clear logs
WatchdogSection: delete one incident
AdvancedSettingsSection: discard section changes
MacroComboPage/useMacroEditor/useComboEditor: discard, delete, reset
```

- [ ] Add one parameterized call-site test per table row: Cancel produces zero
  RPC/local mutation; Confirm produces exactly one; locked mutation remains
  blocked by existing unlock gate.
- [ ] Run full Jest, lint/build, then commit `fix: confirm disruptive Studio actions`.

### Task 8: Update DYA Dependency Pins and Integration Test

**Files:**
- Modify: `dya-studio/package.json`
- Modify: `dya-studio/package-lock.json`

- [ ] Pin exact owner commit SHAs for remediated React/ts-client dependencies.
- [ ] Run:

```bash
npm ci
npm audit --omit=dev
npm run lint
npm test -- --runInBand
npm run build
```

- [ ] Run browser fixtures for malicious device URL, oversized frame, timeout, ambiguous reconnect, support export, and every confirmation path.
- [ ] Commit `build: pin remediated Studio clients`.
