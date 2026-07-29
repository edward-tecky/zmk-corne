# Upstream ZMK Security Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce independently reviewed upstream fixes for ZMK-SEC-009 and ZMK-SEC-021 so BLE Studio and settings-reset can later pass their disabled gates.

**Architecture:** Start from official ZMK `faaf39d9f59cd2a27eca3739cdd9eb197654299b` in a dedicated repository. Make GATT RX writes all-or-nothing before touching the ring, and compile zero-keymap position handling into an explicit rejection path; each finding gets its own tests and commit.

**Tech Stack:** ZMK C, Zephyr ring buffer/GATT APIs, native_sim tests, Twister

## Global Constraints

- Work in `/home/ed/Coding/zmk-security-remediation/zmk`.
- Base exact official SHA `faaf39d9f59cd2a27eca3739cdd9eb197654299b`.
- One finding per commit/review.
- Submit fixes upstream; local product manifest may pin them only after review.
- Do not enable BLE Studio or settings-reset in product artifacts during this plan.
- Run native tests plus affected firmware builds; no flash.

---

## Workspace Setup

```bash
mkdir -p /home/ed/Coding/zmk-security-remediation
git clone https://github.com/zmkfirmware/zmk \
  /home/ed/Coding/zmk-security-remediation/zmk
git -C /home/ed/Coding/zmk-security-remediation/zmk \
  switch -c security-remediation \
  faaf39d9f59cd2a27eca3739cdd9eb197654299b
git -C /home/ed/Coding/zmk-security-remediation/zmk rev-parse HEAD
```

Expected HEAD: `faaf39d9f59cd2a27eca3739cdd9eb197654299b`.

### Task 1: ZMK-SEC-009 — Reject Studio Writes That Cannot Fit

**Files:**
- Modify: `app/src/studio/gatt_rpc_transport.c:63-85`
- Create: `app/tests/studio/gatt-rpc-rx/src/main.c`
- Create: `app/tests/studio/gatt-rpc-rx/CMakeLists.txt`
- Create: `app/tests/studio/gatt-rpc-rx/prj.conf`
- Create: `app/tests/studio/gatt-rpc-rx/testcase.yaml`

**Interfaces:**
- Produces: `zmk_studio_rpc_rx_write(struct ring_buf *, const uint8_t *, uint32_t)` returning full length or `-ENOMEM`; it never partially enqueues.

- [ ] **Step 1: Extract a testable declaration**

Add under `CONFIG_ZTEST` in a private Studio header:

```c
ssize_t zmk_studio_rpc_rx_write(struct ring_buf *rpc_buf,
                                const uint8_t *buf, uint32_t len);
```

- [ ] **Step 2: Write failing ztests**

```c
ZTEST(studio_gatt_rx, test_exact_free_space_is_accepted) {
    zassert_equal(zmk_studio_rpc_rx_write(&ring, payload, 8), 8);
    zassert_equal(ring_buf_size_get(&ring), 8);
}

ZTEST(studio_gatt_rx, test_free_plus_one_is_rejected_without_partial_enqueue) {
    zassert_equal(zmk_studio_rpc_rx_write(&ring, payload, 9), -ENOMEM);
    zassert_equal(ring_buf_size_get(&ring), 0);
}

ZTEST(studio_gatt_rx, test_full_ring_rejects_in_bounded_time) {
    ring_buf_put(&ring, payload, 8);
    zassert_equal(zmk_studio_rpc_rx_write(&ring, payload, 1), -ENOMEM);
    zassert_equal(ring_buf_size_get(&ring), 8);
}
```

- [ ] **Step 3: Run RED**

```bash
west twister -T app/tests/studio/gatt-rpc-rx -p native_sim
```

Expected: helper is undefined.

- [ ] **Step 4: Implement all-or-nothing helper**

```c
ssize_t zmk_studio_rpc_rx_write(struct ring_buf *rpc_buf,
                                const uint8_t *buf, uint32_t len) {
    if (ring_buf_space_get(rpc_buf) < len) {
        return -ENOMEM;
    }

    uint32_t written = ring_buf_put(rpc_buf, buf, len);
    return written == len ? (ssize_t)len : -EIO;
}
```

In `write_rpc_req`, reject nonzero offsets, call helper once, translate negative
result to `BT_GATT_ERR(BT_ATT_ERR_INSUFFICIENT_RESOURCES)`, and notify only after
full success.

- [ ] **Step 5: Run GREEN and boundaries**

```bash
west twister -T app/tests/studio/gatt-rpc-rx -p native_sim
west twister -T app/tests/studio -p native_sim
git diff --check
```

- [ ] **Step 6: Commit**

```bash
git add app/src/studio/gatt_rpc_transport.c \
  app/tests/studio/gatt-rpc-rx
git commit -m "fix(studio): reject RX writes exceeding ring space"
```

### Task 2: ZMK-SEC-021 — Reject Position Events in Zero-Keymap Builds

**Files:**
- Modify: `app/src/keymap.c:704-724`
- Create: `app/tests/keymap/zero-length/src/main.c`
- Create: `app/tests/keymap/zero-length/CMakeLists.txt`
- Create: `app/tests/keymap/zero-length/prj.conf`
- Create: `app/tests/keymap/zero-length/testcase.yaml`
- Create: `app/tests/keymap/zero-length/app.overlay`

**Interfaces:**
- Zero-keymap builds return `-ENOTSUP` before indexing active-layer or binding arrays.

- [ ] **Step 1: Write failing test**

Use overlay with a `zmk,keymap` node containing zero bindings, then:

```c
ZTEST(zero_keymap, test_position_event_is_rejected) {
    zassert_equal(
        zmk_keymap_position_state_changed(0, 0, true, k_uptime_get()),
        -ENOTSUP);
}
```

- [ ] **Step 2: Run RED with warning-as-error**

```bash
west twister -T app/tests/keymap/zero-length -p native_sim \
  --extra-args EXTRA_CFLAGS=-Werror=array-bounds
```

Expected: existing zero-length indexing warning/failure.

- [ ] **Step 3: Compile zero-keymap rejection path**

At function start:

```c
#if ZMK_KEYMAP_LEN == 0
    ARG_UNUSED(source);
    ARG_UNUSED(position);
    ARG_UNUSED(pressed);
    ARG_UNUSED(timestamp);
    return -ENOTSUP;
#else
```

Close with `#endif` before function return/brace so no active-layer array access
is compiled when length is zero.

- [ ] **Step 4: Run GREEN and regression suite**

```bash
west twister -T app/tests/keymap/zero-length -p native_sim \
  --extra-args EXTRA_CFLAGS=-Werror=array-bounds
west twister -T app/tests/studio -p native_sim
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add app/src/keymap.c app/tests/keymap/zero-length
git commit -m "fix(keymap): reject zero-length position events"
```

### Task 3: Upstream and Product Pin Gate

- [ ] Push each commit to a dedicated branch and open separate upstream PRs.
- [ ] Record PR URLs and exact reviewed merge SHAs.
- [ ] Update product frozen manifest only to reviewed merged commits.
- [ ] Re-enable BLE Studio only after ZMK-SEC-009 host tests and encrypted
  hardware boundary tests pass.
- [ ] Restore settings-reset only after its warning-free build, native test, and
  manual recovery test pass.
