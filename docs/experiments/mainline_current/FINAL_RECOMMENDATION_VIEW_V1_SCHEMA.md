# Final Recommendation View v1 Schema

## 定位

本轮只做离线推荐视图，不改 runtime、不改 final decision、不写回 ReviewState。

## 为什么不继续二分类

当前 high-precision support filter 可以把 false accept 压到 0，但只能恢复 1 个 accept。继续用 accept/reject 二分类会把系统的不确定性伪装成确定判断。

## 推荐标签

- `accept_like`: 高质量非 abstract、独立、criterion-grounded 支持足够，且没有 hard negative。
- `borderline_positive`: 有正向支持，但证据质量或维度覆盖不足以安全 accept。
- `reject_like`: 存在 confirmed critical / grounded major / grounded weak core negative。
- `not_assessable`: 缺少真实正向支持与维度 grounding，不应硬判。
- `borderline_insufficient`: 有少量信号，但不足以归入上述类别。

## 论文定位

这比强制 accept/reject 更符合审稿辅助系统：系统应把不确定样本交给人类，而不是默认 reject 或过度 accept。
