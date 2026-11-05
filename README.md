# DeepSeek-V4.1-Flash-1017 on four RTX PRO 6000 Blackwell Server GPUs
[KINGSING 官网原文 / Original article](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Local_AI_Deployment.html)

本仓库为 KINGSING 官网公司新闻的摘要转载与配套技术资料。完整文章首先发表于官网；此处保留脱敏配置、可核查数据和复现说明。**Original publication: KINGSING Company News. This repository contains an attributed summary and supporting technical material.**

测试日期：2026-11-05。硬件为 4 × RTX PRO 6000 Blackwell Server Edition 96 GB、双路 Xeon Platinum 8558P、系统可见 499 GiB 内存。采用 Docker 内的固定 vLLM-Moet 版本、GEMV + P2P、DSpark K3、FP8 ds_mla KV；Engram 约 189.1 GiB 常驻 CPU RAM。

## 最终配对测试 / Paired results

| 指标 | 官方版 | 社区版（abliterated） |
|---|---:|---:|
| 中文生成，中位数 tokens/s | 237.93 | 233.80 |
| 代码生成，中位数 tokens/s | 255.18 | 262.96 |
| 英文生成，中位数 tokens/s | 213.35 | 218.61 |
| GSM8K 200题，关闭思考 | 197/200 | 197/200 |
| GSM8K 200题，low 思考 | 195/200 | 192/200 |
| 综合30题，关闭思考 | 29/30 | 28/30 |
| 综合30题，low 思考 | 30/30 | 30/30 |
| 999,906输入 + 1,024输出，tokens/s | 195.44 | 182.84 |
| 上述长输入首 token 等待，秒 | 217.31 | 217.72 |

短输入每个提示词3轮，表内为解码阶段中位数，不含首 token 等待。百万输入每模型仅1轮；两模型均通过首、中、尾检索。该试验没有证明所有任务的百万上下文质量，也没有验证4路并发百万上下文。社区版不是官方发行版，其名称不等于不拒答保证，本次未评测拒答率。

**209.37 tokens/s 是更早的 GEMV + P2P 候选配置在另一短中文工作负载上的5轮中位数。** 它与上表使用的提示词及测量批次不同，不应直接计算提升比例。FP8 KV 也不应被描述为已经证明“无精度损失”。

## 阅读顺序

1. [完整官网文章](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Local_AI_Deployment.html)：项目背景、发现与局限。
2. [复现说明](文档/复现说明.md)：软硬件版本、构建与运行边界。
3. [测试方法](文档/测试方法.md)：采样、判分和吞吐口径。
4. [配置快照](配置/README.md)、[缓冲区补丁](补丁/README.md)。
5. [公开数据](数据/README.md)：逐轮计时、逐题判分、资源采样及历史结果。

运行 `python 工具/核验公开数据.py` 可离线重算主要汇总并检查数据一致性；它不下载模型，不连接服务器，也不重新做性能测试。

## 来源与使用范围

- [官方模型](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017)
- [社区模型](https://huggingface.co/mrfakename/DeepSeek-V4.1-Flash-1017-abliterated)
- [vLLM-Moet 固定源码](https://github.com/kacper-daftcode/vLLM-Moet/tree/a1d5b5e3ff8230790502e4123017c140d47bc150)
- [GSM8K](https://github.com/openai/grade-school-math/tree/3101c7d5072418e28b9008a6636bde82a006892c)

模型权重、第三方软件和题集的使用受各自上游许可证约束。本仓库不分发模型、完整题集或运行镜像。文章及整理资料版权归 KINGSING；引用实验结论时请注明官网原文和本仓库数据版本。本文没有为第三方材料授予额外许可。
