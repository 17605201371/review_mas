# Accept-Side Evidence Focus v1 Fulltest39 Compare

本文件比较三条 4B fulltest39 运行：clean mainline、Evidence Context Selection v2、Accept-Side Evidence Focus v1。目标不是判断最终 accept/reject，而是看 accept 样本的正向 evidence formation 是否改善。

## 全局指标

| metric | clean mainline | context v2 | focus v1 |
|---|---:|---:|---:|
| predicted accept | 0 | 0 | 0 |
| accept recall | 0.0000 | 0.0000 | 0.0000 |
| real strong support | 21 | 27 | 22 |
| non-abstract strong support | 19 | 24 | 22 |
| empirical strong support | 17 | 18 | 16 |
| fallback strong support | 0 | 0 | 0 |
| rows with 2+ real strong | 6 | 7 | 6 |
| gold accept rows with 2+ real strong | 0 | 2 | 3 |
| evidence turns | 213 | 205 | 184 |
| broad target turns | 193 | 196 | 174 |
| evidence fallback payloads | 2 | 0 | 0 |
| invalid/missing evidence JSON | 18 | 9 | 11 |
| unresolved count | 251 | 226 | 233 |
| evidence gap count | 165 | 156 | 158 |
| patch emitted | 110 | 107 | 82 |
| patch committed | 4 | 3 | 3 |
| rows with any commit | 4 | 3 | 3 |
| legacy controller active turns | 0 | 0 | 0 |

## Gold accept 侧指标

| metric | clean mainline | context v2 | focus v1 |
|---|---:|---:|---:|
| avg payload real strong | 0.3333 | 0.7778 | 1.2222 |
| avg payload real medium | 2.2222 | 1.4444 | 1.8889 |
| rows payload 2+ real strong | 0 | 2 | 4 |
| avg non-abstract strong | 0.3333 | 0.7778 | 1.2222 |
| avg empirical strong | 0.2222 | 0.3333 | 0.5556 |
| avg broad target turns | 4.7778 | 3.7778 | 2.2222 |
| avg unresolved | 5.6667 | 4.5556 | 5.0 |
| avg critique fallback payloads | 0.4444 | 0.8889 | 0.4444 |

## 结论

- `Evidence Context Selection v2` 是全局更稳的输入修复：real/non-abstract support、JSON 稳定性、unresolved/gap 都优于 clean mainline。
- `Accept-Side Evidence Focus v1` 对 gold accept 有局部收益：accept 侧 avg real strong 从 `0.7778` 升到 `1.2222`，rows payload 2+ real strong 从 `2` 升到 `4`，avg broad target turns 从 `3.7778` 降到 `2.2222`。
- 但 Focus v1 也有明显副作用：全局 real strong 从 context v2 的 `27` 降到 `22`，evidence turns 从 `205` 降到 `184`，patch emitted 从 `107` 降到 `82`。这说明 top-2 hard focus 过硬，可能压缩了正常 evidence exploration。
- 三条运行都没有恢复 runtime accept，final decision 仍只能作为 health check，不是本轮主指标。
