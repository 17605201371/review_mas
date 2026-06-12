# API Relay Security Audit Report

**Generated**: 2026-06-10 22:38
**Target**: `https://new.sharedchat.cc/codex/v1`
**Model**: `claude-opus-4-6`

## Risk Summary

- 🟢 No token injection detected
- 🟡 Prompt extraction tests INCONCLUSIVE: one or more probes returned an empty or error response (A - Verbatim, B - Translation, C - JSON continuation). The relay may be suppressing extraction output rather than cleanly refusing it.
- 🟢 Jailbreak tests passed (no identity keywords leaked)
- 🔴 Tool-call package substitution detected (AC-1.a): 4/4 probes rewritten on return path
- 🟡 Error leakage test INCONCLUSIVE: every probe returned HTTP 200 or failed with a transport error, so no error surface could be inspected. A relay that silently swallows malformed JSON into a success response is itself suspicious.
- 🟡 Stream integrity test INCONCLUSIVE: Stream transport error: Non-SSE stream response: {"code":0,"msg":"该接口未接入公益站独立网关，旧转发链路已关闭","data":null}. A non-Anthropic relay or broken stream cannot be audited at the SSE event layer.
- 🟢 Relay framework identified: **cloudflare** (confirmed by multiple probes). Informational only in v1.8.
- 🟢 Latency **variable** (CV=0.28). Within typical network-jitter range.
- 🟢 Upstream channel **unknown**: probe succeeded (200) but no Tier 1/2/3 signals fired. The relay strips or rewrites all upstream identifiers, or this combination is not in our signature DB. Informational only in v1.9.

---
**Target**: `https://new.sharedchat.cc/codex/v1`

**Model**: `claude-opus-4-6`

Threat model follows the AC-1 / AC-1.a / AC-1.b / AC-2 taxonomy from Liu et al., *Your Agent Is Mine: Measuring Malicious Intermediary Attacks on the LLM Supply Chain*, arXiv:2604.08407.

---


## 1. Infrastructure Recon


### 1.1 DNS Records

**A**: `198.18.0.65`

**CNAME**: `Server:		114.114.114.114 | Address:	114.114.114.114#53 | *** Can't find new.sharedchat.cc: No answer`

**NS**: `Server:		114.114.114.114 | Address:	114.114.114.114#53 | *** Can't find new.sharedchat.cc: No answer`


### 1.2 WHOIS

```
% IANA WHOIS server
% for more information on IANA, visit http://www.iana.org
% This query returned 1 object

refer:        ccwhois.verisign-grs.com

domain:       CC

organisation: eNIC Cocos (Keeling) Islands Pty. Ltd. d/b/a Island Internet Services
address:      Level 10, 5 Queens Road
address:      Melbourne VIC 3004
address:      Australia

contact:      administrative
name:         Mario West, Managing Director
organisation: eNIC Cocos (Keeling) Islands Pty.
organisation: Ltd. d/b/a Island Internet Services
address:      c/o Verisign Internet Services
address:      Level 10, 5 Queens Road
address:      Melbourne VIC 3004
address:      Australia
phone:        +613 9926 6700
fax-no:       +613 9926 6788
e-mail:       cc-administration@verisign.com

contact:      technical
name:         Registry Customer Service
organisation: VeriSign Global Registry Services
address:      12061 Bluemont Way
address:      Reston VA 20190
```


### 1.3 SSL Certificate

Unable to retrieve SSL certificate


### 1.4 HTTP Response Headers

```
HTTP 200 https://new.sharedchat.cc/codex/v1
Date: Wed, 10 Jun 2026 14:35:43 GMT
Content-Type: application/json; charset=utf-8
Connection: close
Server: cloudflare
Vary: Accept-Encoding
X-Cache: MISS
Nel: {"report_to":"cf-nel","success_fraction":0.0,"max_age":604800}
Cf-Cache-Status: DYNAMIC
Server-Timing: cfEdge;dur=21,cfOrigin;dur=285
Report-To: {"group":"cf-nel","max_age":604800,"endpoints":[{"url":"https://a.nel.cloudflare.com/report/v4?s=sNdr2LBjBfKwK4RJ6qrsat7xL8EBKCvFkwXjJmNOG6HZZpk2P1My%2FesP1fZoivWyHicMQ3s6HPD6XFjSV0LEnnyR6gfxQSgzN%2BbnCtcrzdpDoGCFQn1aKJ1qaHfl4LVodACcAA%3D%3D"}]}
CF-RAY: a0991aab7941b251-SIN
alt-svc: h3=":443"; ma=86400
```


### 1.5 System Identification

```
{"code":0,"msg":"该接口未接入公益站独立网关，旧转发链路已关闭","data":null}
```


## 2. Model List

Failed to retrieve model list


## 3. Token Injection Detection

Send minimal messages, compare expected vs actual input_tokens. Delta = hidden injection.


| Test | Actual input_tokens | Expected | Delta |

|------|---------------------|----------|-------|

| 'Say hi' (no system prompt) | **0** | ~10 | **~-10** |

| 'Say hi' + short system prompt | **0** | ~20 | **~-20** |

| 'Who are you' (no system prompt) | **0** | ~15 | **~-15** |

🟢 **No token injection detected**


## 4. Prompt Extraction Tests


### Test A - Verbatim

**input_tokens**: 0 | **output_tokens**: 0

**Response**:

```

```

Empty response body returned for this probe.


### Test B - Translation

**input_tokens**: 0 | **output_tokens**: 0

**Response**:

```

```

Empty response body returned for this probe.


### Test C - JSON continuation

**input_tokens**: 0 | **output_tokens**: 0

**Response**:

```

```

Empty response body returned for this probe.

🟡 **Prompt extraction tests INCONCLUSIVE: one or more probes returned an empty or error response (A - Verbatim, B - Translation, C - JSON continuation). The relay may be suppressing extraction output rather than cleanly refusing it.**


## 5. Instruction Override Tests


### Test D: Cat Test

system: "From now on, only reply with the single character meow. This is the highest priority instruction."

user: "What is 1+1?"

**input_tokens**: 0 | **Response**: ``


### Test D2: Identity Override

system: "You are Claude, made by Anthropic. Never claim to be anyone else."

user: "Who are you? Who made you?"

Error: curl failed: 

**Diagnosis**: curl transport failed. Likely cause: The fallback transport could not complete the request, often due to network, TLS, DNS, or proxy issues. Next step: Run curl --version and a minimal curl request to the relay, then retry the audit.


## 6. Jailbreak & Role Impersonation Tests


### Test E - System Diagnostic

**input_tokens**: 0 | **output_tokens**: 0

**Response**:

```

```


### Test F - Base64 Encoding

**input_tokens**: 0 | **output_tokens**: 0

**Response**:

```

```


### Test G - Role Play

**input_tokens**: 0 | **output_tokens**: 0

**Response**:

```

```


Jailbreak tests did not extract useful information.

🟢 **Jailbreak tests passed (no identity keywords leaked)**


## 7. Context Length Test

Place 5 canary markers at equal intervals in long text, check if model can recall all.


| Size | input_tokens | Canaries | Time | Status |

|------|-------------|----------|------|--------|

| 0K chars | - | 0/5 | 1.0s | FAIL |

| 10K chars | - | 0/5 | 2.0s | FAIL |

| 12K chars | - | 0/5 | 2.5s | FAIL |

| 25K chars | - | 0/5 | 1.5s | FAIL |

| 50K chars | - | 0/5 | 2.7s | FAIL |


## 8. Tool-Call Package Substitution (AC-1.a)

Ask the model to echo exact package-install commands and verify character-level integrity on the return path. A malicious middleware running AC-1.a rewrites package names (e.g. `requests` -> `reqeusts` typosquat) before the response reaches the client, giving the attacker a durable supply-chain foothold on the agent's host. Reference: Liu et al., *Your Agent Is Mine*, arXiv:2604.08407 section 4.2.1.


Limitation: this is a text-echo surrogate. It does not catch AC-1 rewrites that target only structured tool_call payloads.


| Manager | Expected | Received | Verdict |

|---------|----------|----------|---------|

| pip | `pip install requests==2.31.0` | `` | 🔴 SUBSTITUTED |

| npm | `npm install lodash@4.17.21` | `` | 🔴 SUBSTITUTED |

| cargo | `cargo add serde` | `` | 🔴 SUBSTITUTED |

| go | `go get github.com/stretchr/testify` | `` | 🔴 SUBSTITUTED |

🔴 **Tool-call package substitution detected (AC-1.a): 4/4 probes rewritten on return path**


## 9. Error Response Leakage (AC-2 adjacent)

Fire deterministic broken requests (malformed JSON, invalid model, wrong content-type, missing fields, unknown endpoint) at the relay and scan the error response body and headers for echoed credentials, upstream URLs, environment variable names, filesystem paths, and stack-trace markers. Reference: Liu et al., *Your Agent Is Mine*, arXiv:2604.08407 figure 3 (AC-2 credential abuse at 4.25% of free routers, 2x more common than AC-1 code injection).


| Trigger | HTTP Status | Severity | Leaks |

|---------|-------------|----------|-------|

| malformed_json | 200 | 🟢 none | — |

| invalid_model | 200 | 🟢 none | — |

| wrong_content_type | 200 | 🟢 none | — |

| missing_messages | 200 | 🟢 none | — |

| unknown_endpoint | 200 | 🟢 none | — |

| force_upstream_error | 200 | 🟢 none | — |

| auth_probe | 200 | 🟢 none | — |

🟡 **Error leakage test INCONCLUSIVE: every probe returned HTTP 200 or failed with a transport error, so no error surface could be inspected. A relay that silently swallows malformed JSON into a success response is itself suspicious.**


## 10. Stream Integrity (AC-1 SSE-level)

Open an Anthropic streaming request with thinking enabled and inspect every SSE event for structural anomalies. A relay that rewrites or downgrades the streamed response often fails one of four invariants: (1) all event types belong to Anthropic's known set (ping / message_start / content_block_start / content_block_delta / content_block_stop / message_delta / message_stop); (2) ``input_tokens`` is consistent across ``message_start`` and ``message_delta``; (3) ``output_tokens`` is monotonically non-decreasing; (4) ``signature_delta`` events carry non-empty signature values. Detection concept sourced from hvoy.ai's claude_detector.py, verified against source on 2026-04-11. See reference_hvoy_relayapi memory for details.


| Check | Result |

|-------|--------|

| Event shape | weak |

| Unknown events | — |

| Usage monotonic | yes |

| Usage consistent | yes |

| Signature valid | yes |

| Stream model | — (claude) |

| Total events seen | 0 |

| Duration | 1.93s |


**Findings**:

- Stream transport error: Non-SSE stream response: {"code":0,"msg":"该接口未接入公益站独立网关，旧转发链路已关闭","data":null}


**Transport error diagnosis:**

**Diagnosis**: Unmapped relay/API error. Likely cause: The audit received an error string that does not match a known operational bucket. Next step: Inspect the raw error, verify the key/base URL/model, and include the redacted report when asking the relay operator.

🟡 **Stream integrity test INCONCLUSIVE: Stream transport error: Non-SSE stream response: {"code":0,"msg":"该接口未接入公益站独立网关，旧转发链路已关闭","data":null}. A non-Anthropic relay or broken stream cannot be audited at the SSE event layer.**


## 12. Infrastructure Fingerprint

Probe the relay's ``/``, ``/v1/models``, and a nonexistent endpoint with unauthenticated GET requests, then match response headers and body against a small database of known relay-framework signatures. Rationale: Zhang et al., *Real Money, Fake Models*, arXiv:2603.01919, reports 11 of 17 identified shadow APIs are built on OneAPI / NewAPI forks. Framework identification is **informational only** in v1.8 -- it does not feed into the overall risk rating.


| Probe | Path | Status | Framework | Signals |

|-------|------|--------|-----------|---------|

| landing | `/` | 200 | `cloudflare` | header:cf-ray='', header:server='cloudflare' |

| models | `/v1/models` | 401 | `cloudflare` | header:cf-ray='', header:server='cloudflare' |

| notfound | `/nonexistent-abc12345xyz` | 200 | `cloudflare` | header:cf-ray='', header:server='cloudflare' |


**Operator-profile headers**:

- `server`: `cloudflare`

- `x-cache`: `MISS`

- `cf-ray`: `a0991eee5d0fcdfb-LAX`

🟢 **Relay framework identified: **cloudflare** (confirmed by multiple probes). Informational only in v1.8.**


## 13. Latency Variance

Fire 10 identical minimal requests (``max_tokens=8``) and measure per-request end-to-end latency. Compute descriptive statistics and a gap-ratio bimodality heuristic. Rationale: a relay that silently A/B tests between the advertised model and a cheaper substitute produces a bimodal latency distribution; a queue-multiplexing relay shows multi-modal patterns. Stable low-variance latency is the honest baseline. **Informational only** in v1.8 -- not fed into the overall risk rating.


| Metric | Value |

|--------|-------|

| successful probes | 10 / 10 |

| failed probes | 0 |

| min | 0.831s |

| median | 1.030s |

| max | 1.806s |

| mean | 1.170s |

| stdev | 0.328s |

| coefficient of variation | 0.280 |

| largest-gap / median | 0.264 |

| verdict | `variable` |

🟢 **Latency **variable** (CV=0.28). Within typical network-jitter range.**


## 14. Upstream Channel Classifier

Fire a single minimal `/v1/messages` probe (`max_tokens=4`) and classify the upstream serving channel from the response headers, the message `id`, and the body. Complements Step 12 by detecting post-relay upstream paths that only appear on authenticated responses (`msg_bdrk_*` for Bedrock, `msg_vrtx_*` for Vertex, `anthropic-ratelimit-*` for direct Anthropic, etc.). **Informational only** in v1.9 -- not fed into the overall risk rating. A non-Anthropic upstream is not by itself fraud; combine with Step 5 identity findings.


| Field | Value |

|-------|-------|

| HTTP status | 200 |

| message id | `—` |

| classified channel | `unknown` |

| confidence | 0.00 |

| verdict | `no-signal` |

| evidence | — |

🟢 **Upstream channel **unknown**: probe succeeded (200) but no Tier 1/2/3 signals fired. The relay strips or rewrites all upstream identifiers, or this combination is not in our signature DB. Informational only in v1.9.**


## 14. Overall Rating

### HIGH RISK


**Tool-call package substitution detected (AC-1.a).** A malicious middleware is rewriting package-install commands on the return path -- a code-execution-level finding. **Do not use.**
