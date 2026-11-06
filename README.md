# DeepSeek-V4.1-Flash-1017 on four RTX PRO 6000 Blackwell Server GPUs
[KINGSING 官网原文 / Original article](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Local_AI_Deployment.html)

本仓库为 KINGSING 官网公司新闻的摘要转载与配套技术资料。完整文章首先发表于官网；此处保留脱敏配置、可核查数据和复现说明。**Original publication: KINGSING Company News. This repository contains an attributed summary and supporting technical material.**

## 2026-11-07 更新：W4A8 融合与冷预填充优化

**当前默认已切换为 W4A8 融合 + DSpark K5（standard），适合单任务中文/代码输出；K3 保留为并发优先的已验证选择。** 本轮仅测试相同的社区修改版权重，不将结果归到官方原始权重上。性能实验于11月6日完成，上线验收于11月7日完成（北京时间）。

| Workload / metric | Original A16 K3 | W4A8 K3 | W4A8 K5 |
|---|---:|---:|---:|
| 1 request(s), Chinese decode tok/s | 228.54 | 240.54 | 269.24 |
| 1 request(s), Code decode tok/s | 255.72 | 272.39 | 327.75 |
| 1 request(s), English decode tok/s | 219.80 | 253.79 | 243.15 |
| 4 request(s), Chinese aggregate tok/s | 485.63 | 520.66 | 487.38 |
| 4 request(s), Code aggregate tok/s | 525.68 | 586.79 | 530.41 |
| 4 request(s), English aggregate tok/s | 471.29 | 506.30 | 441.54 |
| 8 request(s), Chinese aggregate tok/s | 489.33 | 810.04 | 712.34 |
| 8 request(s), Code aggregate tok/s | 517.88 | 850.97 | 800.10 |
| 8 request(s), English aggregate tok/s | 464.50 | 733.77 | 678.77 |
| 128,000-token cold TTFT (seconds) | 27.29 | 6.86 | 6.86 |
| 1,000,000-token cold TTFT (seconds) | 222.55 | 55.40 | 55.33 |

相对本轮同提示词原配置，K5单路中文提升17.8%、代码提升28.2%；K3八路聚合提升58.0%–65.5%。百万输入冷首字等待从222.55秒降至K5的55.33秒，减少75.1%。K5并非所有任务最快：单路英文和多路吞吐通常由K3领先。并发表为总吞吐，不是每路速度。

本轮含10组配置与1次实验后原配置对照，共1,353次测速请求。C1每类5次，C4/C8每类3批；关闭思考，输出上限1,024，temperature=0、seed=731。冷预填充每长度2次，首部唯一盐值，缓存命中增量为0。实验前后原配置单路中位变化不超过0.50%，八路聚合不超过2.47%。

两档W4A8候选的GSM8K chat均197/200，与基线同分同错题；混合chat为29/30（基线28/30），low为30/30；应用10项与合成图片2项通过。A16加速组和K4曾出现196/200，未剔除失败；原配置重复也能触发相同的截断/理解波动。有限样本不构成普遍质量等价证明，本轮未重跑GSM8K low，不覆盖最高思考档或LobeChat端到端任务耗时。

共同设置：TP4、1,048,576上下文、FP8 KV 6 GiB/GPU、seqs=8、batch=8192、graph上限64、indexer分片阈值2048、prefill SP/fast、fused MoE和公平预填充。**强制A16必须设为0，相关W4A8融合路径才会进入。** TARGET_LM_HEAD_MXFP8和SM120_GEMV_BMM均保持0；block rejection未见明确优势，保留standard。八路测试使用短输入，不代表八路独立百万上下文容量。

上线后另做每类3次单路复测：中文 276.21、代码 327.34、英文 229.30 tok/s；实际容器参数与验收候选匹配，接口别名、应用和图像检查通过。该小样本上线检查与上表5轮A/B分开报告。

- [完整实验经验与取舍](文档/第三轮优化经验.md)
- [W4A8两档配置快照](配置/第三轮W4A8配置.json)
- [脱敏逐次计时与评分](数据/2026-11-06-第三轮实测.json)
- 离线复算：`python 工具/核验第三轮数据.py`。历史数据继续用原核验脚本。

历史批次测试日期：2026-11-05。硬件为 4 × RTX PRO 6000 Blackwell Server Edition 96 GB、双路 Xeon Platinum 8558P、系统可见 499 GiB 内存。采用 Docker 内的固定 vLLM-Moet 版本、GEMV + P2P、DSpark K3、FP8 ds_mla KV；Engram 约 189.1 GiB 常驻 CPU RAM。

## 2026-11-05 历史官方/社区版对照 / Historical paired results

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
