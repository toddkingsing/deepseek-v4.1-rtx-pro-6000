# KINGSING Runs 24 Million-Token DeepSeek-V4.1-Flash-1017 Sessions on Eight RTX PRO 6000 GPUs

[Original publication: KINGSING](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Eight_GPU_24_Million_Token_Contexts.html)

KINGSING has completed an eight-GPU deployment evaluation of DeepSeek-V4.1-Flash-1017, demonstrating 24 independent sessions with 1,000,004 input tokens each resident and generating together for 60.18 seconds. Aggregate output during that shared window was 755.09 tokens/s, with individual streams at 26.66–35.60 tokens/s. All 24 random-fact retrieval checks passed, with zero initial prefix-cache hits.

The principal gain over our previous four-GPU service is long-context capacity, followed by multi-request throughput. Single-request Chinese and code generation became slightly slower, English became slightly faster, and the numerical precision settings were retained. When all 24 million-token inputs started cold, the slowest first content token arrived after 1,439.22 seconds—about 24 minutes. Capacity should not be confused with low cold-start latency.

These are measurements of mrfakename/DeepSeek-V4.1-Flash-1017-abliterated, revision 517efab9ccfef7f714dbd7d679f181a86f43ccf9. They are not new benchmarks of the official, unmodified DeepSeek checkpoint. The community model name is not a guarantee about refusal behavior; refusal rates were not evaluated. This publication uses completed historical measurements and introduces no new inference tests.

## How the eight GPUs are used

The server uses eight RTX PRO 6000 Blackwell Server Edition GPUs, with all eight observed at PCIe 5.0 ×16 under load. TP4×PP2 means two pipeline stages, each using four-way tensor parallelism: main transformer layers 0–19 are on the first four GPUs and layers 20–39 on the second four. Together they serve one model. The model has 40 main layers; three separate DSpark auxiliary prediction layers do not change that main-layer count.

| Setting | Previous four-GPU service | Selected eight-GPU service |
| --- | --- | --- |
| Parallelism | TP4 | TP4 × PP2, 20/20 layers |
| Expert / KV precision | W4A8 / FP8 DS MLA | W4A8 / FP8 DS MLA |
| CPU Engram offload | Enabled | Enabled, approximately 188.83 GiB |
| KV budget per GPU | 6 GiB | 36 GiB |
| Total configured GPU KV budget | 24 GiB | 288 GiB |
| Input + output window per request | 1,048,576 tokens | 1,048,576 tokens |
| Scheduler sequence limit | 8 | 24 |
| DSpark draft length | Fixed K5 | K5 for batches1–4; K3 for batches5–32 |
| Decode CUDA graph limit | 64 | 128; corrected graph-bucket dispatch |

CPU offload was already present in the four-GPU production service. The capacity gain therefore must not be attributed to newly introducing offload. Distributing the same model across more devices leaves substantially more space for KV caches. The eight-GPU startup report gives 25,981,641 cached tokens, or 24.78 theoretical full windows; the measured 24-session result is separate evidence. We do not claim that doubling VRAM by itself guarantees this multiplier on other systems.

The final runtime retains BF16 as the global dtype, uses the W4A8 expert path and GEMV, standard rejection with probabilistic DSpark drafts, outer FULL_DECODE_ONLY graphs and native breakable graphs. SP/GATHER/PIPE prefill changes and optional inner PP2 replay graphs are disabled in the selected profile. There is no new FP4 KV conversion, Engram requantization or GPU overclock.

## Generation speed against the four-GPU production baseline

The following table uses the same short-prompt families, sampling settings and scoring conventions. One request reports median decode rate; four and eight requests report aggregate output divided by batch wall time. Aggregate throughput is not each user’s output rate. Measurements use temperature 0, seed 731, thinking disabled and a 1,024-token output budget. The groups were measured sequentially, not as a randomized crossover; small changes are descriptive, not statistical significance claims.

| Concurrent requests | Task | Four GPUs, tok/s | Eight GPUs, tok/s | Change |
| --- | --- | --- | --- | --- |
| 1 | chinese | 277.15 | 260.72 | -5.93% |
| 1 | code | 321.77 | 310.25 | -3.58% |
| 1 | english | 243.56 | 248.35 | +1.97% |
| 4 | chinese | 472.92 | 512.81 | +8.43% |
| 4 | code | 534.56 | 615.82 | +15.20% |
| 4 | english | 439.17 | 488.00 | +11.12% |
| 8 | chinese | 692.74 | 855.94 | +23.56% |
| 8 | code | 788.79 | 935.43 | +18.59% |
| 8 | english | 667.05 | 779.00 | +16.78% |

Compared with the original production K5 baseline, eight-request throughput improved by 16.78–23.56%, while single-request Chinese and code rates fell by 5.93% and 3.58%. A post-power-rewiring four-GPU control gives single-request changes of −4.40%, −6.15% and +2.97% for Chinese, code and English. Both baseline sets are included in the public data; we do not select the most favorable baseline independently for each claim.

This is a whole-deployment comparison, not a measurement of GPU count alone. A prior four-GPU fixed-K3 experiment reached eight-request aggregate rates of 810.04/850.97/733.77 tokens/s for Chinese/code/English. The final eight-GPU rates are about 5.7%/9.9%/6.2% above those historical concurrency-oriented values. The formal four-GPU production baseline used K5 to favor single-request performance; dynamic K contributes to the new deployment’s balance.

## Independent million-token sessions: capacity and waiting time

| Sessions | Input tokens each | Shared generation, s | Aggregate tok/s | Per-stream tok/s | Cold TTFT median, s | Cold TTFT max, s |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 1,040,004 | 61.01 | 583.30 | 51.63–62.35 | 486.85 | 623.56 |
| 24 | 1,000,004 | 60.18 | 755.09 | 26.66–35.60 | 831.47 | 1439.22 |

Each request used an independent salted context. All streams had to be resident, have zero waiting requests and continue generating throughout the shared measurement window without preemption. Retrieval and actual API token usage were checked. Streams were intentionally cancelled after the measurement window and cleanup was verified; this is not a claim that every request generated to the maximum context limit. The 24-session result is also not 24 simultaneous inputs of exactly 1,048,576 tokens: the context window includes output.

The four-GPU startup log reported 2,857,448 cached tokens and 2.73 theoretical full windows. We do not have an equivalent archived three-session, independent million-input, simultaneous 60-second acceptance record. Consequently, we do not advertise a rigorously measured “three to 24” or “eightfold concurrency” improvement. The current 24-session result is directly measured; neither max_num_seqs nor rounding a theoretical window count proves capacity.

The long-context capacity test traversed an HTTPS domain, Nginx and a PHP relay on a private network. It was not a public-Internet load test. Cold prefill involves scheduling and resource contention: a long delay before all streams begin is compatible with successful concurrent generation once their contexts are resident.

## Prefill and mixed workloads remain important trade-offs

The final single-request nominal-million prefill tests had a median first-token delay of 61.14 seconds across three cold repeats; actual prompt lengths were 999,934–999,939 tokens. A separate relay test with 1,000,004 actual input tokens measured 61.17 seconds to first content and 416.32 tokens/s during 60.55 seconds of subsequent generation. Its prompt and output differ from the short-prompt benchmarks, so 416.32 must not be used to claim a short-input speedup.

Historical four-GPU million-input medians were 55.73 seconds in the November 7 baseline,65.59 seconds in the November 8 production baseline and 65.99 seconds in the rewired control. The final result is about 6.8–7.4% faster than the latter two and 9.7% slower than the earlier batch. It supports a roughly one-minute single cold million-input latency, not a universal prefill speedup.

With ten 128K sessions already generating, adding a new million-input request gave 62.95 seconds to first content. Existing-stream aggregate output fell from 909.81 tokens/s before competing prefill to 159.33 during prefill, then recovered to 991.06. Their cached fact checks passed afterward. More KV capacity does not remove compute contention from large new inputs; no matched four-GPU result is available for this mixed workload.

## Quality was retained broadly, not proven identical

| Evaluation | Four-GPU baseline | Final eight-GPU profile |
| --- | --- | --- |
| GSM8K fixed200-question subset, chat | 197/200 | 197/200 |
| Authored short tasks, chat | 29/30 | 28/30 |
| Authored short tasks, low thinking | 30/30 | 30/30 |
| Application checks | 10/10 | 10/10 |
| Short synthetic image checks | 2/2 | 2/2 |
| Long text checks | No complete matched set | 12/12 |
| Long image/text checks | No complete matched set | 4/4 at19,037 input tokens |

All 200 scored GSM8K answers match the four-GPU reference, including its three errors. The ordinary short-task regression remains visible: one fewer correct answer. Long-text checks covered ten approximately 163K and two approximately 1M inputs, split between chat and low-thinking modes. Retrieval success does not establish universal million-token reasoning quality. We did not run complete MMLU/GPQA, compare against unquantized original weights, or prove bitwise logits equivalence.

Matched eight-GPU A8-to-A16 trials slowed single-request generation by 10.66–19.42% and ten-request throughput by 29.53–33.75%. Disabling GEMV slowed Chinese/code single-request generation by 14.75%/16.64%; a full quality study of that candidate was not completed. Neither change established a worthwhile quality improvement within the accepted 10% slowdown budget. A16 changes activation precision, not the original quantized expert weights.

A final fixed-seed temperature check also matters for everyday sampling: temperature 1 was 2.44–7.41% slower than temperature 0 for single requests and 1.62–3.38% slower for ten-request batches. The short-task scores were 27/30 and 28/30 respectively. These finite checks do not prove that speculative sampling has the same distribution as a separate non-speculative reference.

## Rejected optimizations and operational safeguards

A PIPE2 candidate improved isolated prefill but later failed ten independent 1.04M cold inputs with a P2P receive timeout. It was rejected. GATHER with expanded KV failed the combined throughput and cleanup criteria; optional inner PP2 replay gave essentially no mean short-batch gain and was not selected. Published final numbers come from the selected non-PIPE runtime, not the fastest isolated results from failed candidates.

A local P2P safety patch changes five receive-timeout branches from continuing after timeout to an explicit CUDA device trap. Two zero-peer identity checks and five isolated fault-injection cases passed. The identity checks are not a complete old/new numerical equivalence test, and the patch does not claim to fix every communication-timeout cause. The five documented Xid 43 events were intentional fault injections; other unexpected kernel hardware events were not observed in the monitored interval.

An independent Claude Code review and a follow-up review informed the timeout, launcher and relay work. The selected service has bounded eight-GPU restart handling and an engine-health watchdog; failures do not silently reduce it to four GPUs. Decision and mock integration tests were completed, but the final serving worker was not deliberately crashed to demonstrate recovery.

The relay now has a dedicated static 32-worker PHP-FPM pool, a 3,500-second model cURL total timeout and 3,600-second FPM limit, streaming heartbeats, explicit stream-error handling and cancellation cleanup. Client-side deadlines must also permit long first-token waits. Non-streaming disconnects may not be detected immediately, and multi-round search shares the FPM total deadline. A32-worker pool is not evidence of 32 million-context model sessions.

## Monitoring scope, reproducibility and what was not tested

Hardware sampling covered 7.24 hours across the tuning process, with 883 samples; this is not 7.24 hours of continuous full load on the final profile. The final profile reached a sampled maximum of 71°C and 2,315.39W summed GPU draw, with no container OOM, container swap use or unexpected restart at final validation. These are sampled GPU values, not whole-server wall power or an electrical sizing guarantee.

The planned one-hour 24-client stability soak was explicitly cancelled by the operator and was not executed or counted as passed. The simultaneous 60-second capacity result is not a substitute for long-duration stability evidence. Some optional NCCL graph-rewrite warnings were caught with fallback to the original graph, so the logs must not be described as containing no CUDA warnings. No concurrency above 24 was pursued.

The runtime reports vLLM 0.32.1 rc 1.dev 117+gdf 3 bd 094 a and PyTorch 2.14.0+cu 130, based on a pinned vLLM nightly plus Moet, modified Python sources and selected CUDA extensions. It is not a full vLLM/PyTorch source rebuild. The published configuration identifies the local image by content ID, but that ID is not a downloadable registry image. The repository does not provide the complete eight-GPU build, every local patch, or a verified one-command installer; no second-host rebuild is claimed.

The supporting repository publishes sanitized per-batch timing and capacity measurements, scored GSM8K answers without full question texts, configuration settings and an offline arithmetic checker. Private addresses, API endpoints, credentials, host paths, full operational logs and model weights are excluded. The checker reads existing data only and does not call a model.

- [Previous four-GPU KINGSING article](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Local_AI_Deployment.html)
- [Supporting GitHub repository](https://github.com/toddkingsing/deepseek-v4.1-rtx-pro-6000)
- [Detailed English article on GitHub](https://github.com/toddkingsing/deepseek-v4.1-rtx-pro-6000/blob/main/文档/eight-gpu-24x1m.md)
- [Community checkpoint and its license](https://huggingface.co/mrfakename/DeepSeek-V4.1-Flash-1017-abliterated)
- [Upstream vLLM-Moet](https://github.com/kacper-daftcode/vLLM-Moet)
- [GSM8K dataset](https://github.com/openai/grade-school-math/tree/3101c7d5072418e28b9008a6636bde82a006892c)

Original publication: KINGSING Company News, November 9, 2026. DeepSeek, the community model maintainer, vLLM-Moet, vLLM, FlashInfer, PyTorch and GSM8K contributors retain their respective attribution and licensing. The findings describe this local deployment and do not imply endorsement or universal performance guarantees.
