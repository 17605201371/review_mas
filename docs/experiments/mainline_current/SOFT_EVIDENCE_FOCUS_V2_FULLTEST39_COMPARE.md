# Soft Evidence Focus v2 Fulltest39 Compare

本文件比较 clean mainline、Evidence Context v2、hard Focus v1 与 Soft Focus v2。Soft Focus v2 是本轮主结果：保留 preferred claims，但不再把 allowed claims 硬截断成 top-2。

## 全局指标

| metric | clean mainline | context v2 | hard focus v1 | soft focus v2 |
|---|---:|---:|---:|---:|
| pred accept | 0 | 0 | 0 | 1 |
| accept recall | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| reject recall | 1.0000 | 1.0000 | 1.0000 | 0.9667 |
| accuracy | 0.7692 | 0.7692 | 0.7692 | 0.7436 |
| macro-F1 | 0.4348 | 0.4348 | 0.4348 | 0.4265 |
| real strong | 21 | 27 | 22 | 40 |
| non-abstract strong | 19 | 24 | 22 | 39 |
| empirical strong | 17 | 18 | 16 | 33 |
| fallback strong | 0 | 0 | 0 | 0 |
| rows 2+ real strong | 6 | 7 | 6 | 11 |
| gold accept rows 2+ real strong | 0 | 2 | 3 | 3 |
| evidence turns | 213 | 205 | 184 | 222 |
| broad target turns | 193 | 196 | 174 | 207 |
| evidence fallback payloads | 2 | 0 | 0 | 0 |
| invalid/missing evidence JSON | 18 | 9 | 11 | 31 |
| JSON fallback used | 1 | 0 | 0 | 0 |
| unresolved | 251 | 226 | 233 | 167 |
| evidence gaps | 165 | 156 | 158 | 149 |
| flaws | 60 | 57 | 56 | 49 |
| patch emitted | 110 | 107 | 82 | 125 |
| patch committed | 4 | 3 | 3 | 8 |
| rows with commit | 4 | 3 | 3 | 8 |
| legacy controller active turns | 0 | 0 | 0 | 0 |

## Gold accept 侧指标

| metric | clean mainline | context v2 | hard focus v1 | soft focus v2 |
|---|---:|---:|---:|---:|
| avg payload real strong | 0.3333 | 0.7778 | 1.2222 | 1.8889 |
| avg non-abstract strong | 0.3333 | 0.7778 | 1.2222 | 1.5556 |
| avg empirical strong | 0.2222 | 0.3333 | 0.5556 | 1.1111 |
| rows payload 2+ real strong | 0 | 2 | 4 | 5 |
| avg broad target turns | 4.7778 | 3.7778 | 2.2222 | 4.1111 |
| avg unresolved | 5.6667 | 4.5556 | 5.0000 | 4.2222 |
| avg critique fallback payloads | 0.4444 | 0.8889 | 0.4444 | 0.8889 |

## Soft Focus v2 直接结论

- Soft Focus v2 基本恢复了旧 empirical structuring 的 support formation 强度，同时保持旧 controller 污染为 0：`real_strong=40`、`nonabstract=39`、`empirical=33`、`legacy_controller_active_turns=0`。
- 与 Context v2 相比，Soft Focus v2 的 support formation 明显更强，unresolved / evidence gaps / flaw count 也更低。
- 与 hard Focus v1 相比，Soft Focus v2 没有压缩全局 support，说明“软偏置而不是硬截断”是正确方向。
- 风险是 evidence JSON invalid/missing 从 Context v2 的 `9` 升到 `31`，且 runtime 出现 1 个 false accept：`NnExMNiTHw`。这说明 Soft Focus v2 可以进入候选主线，但 final recommendation 必须继续走 derived / calibrated policy，不能直接相信 runtime accept。
