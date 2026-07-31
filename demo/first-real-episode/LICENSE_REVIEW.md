# First real episode license review

This file separates **technical pipeline validation** from **commercial release clearance**.

## Original project-owned material

The following demo material was written specifically for this repository and does not intentionally reproduce an existing series, character, celebrity, logo, song, or sound recording:

- the `ورشة النور` series bible;
- عمر and نادر character descriptions and visual prompts;
- the workshop location and emergency-lamp episode premise;
- all continuity and direction constraints;
- the procedural ambience, effects, and chord-score source code.

Generated outputs still require human review for accidental resemblance, logos, watermarks, or memorized material before publication.

## Runtime and model review

| Component | Baseline source | Technical use in demo | Release review required |
|---|---|---|---|
| Qwen3-8B GGUF | Official Qwen model repository | Story, screenplay, and direction JSON | Preserve model license and notices in the release evidence bundle. |
| llama.cpp | Official ggml-org repository | Local OpenAI-compatible inference server | Preserve the runtime license and notices. |
| SDXL Base 1.0 | Official Stability AI model repository | Character references, workshop, and keyframes | Review the model license, acceptable-use terms, and generated images before release. |
| SVD 1.1 XT | Official Stability AI model repository | Short image-to-video clips | Accept repository access terms and review the current Stability license before any commercial release. |
| Piper runtime | Official Open Home Foundation Piper repository/package | CPU Arabic speech synthesis | Preserve the runtime license and notices. |
| `ar_JO-kareem-medium` voice | Official Piper voices repository | Arabic demo voices | The voice model card points to a source dataset/license URL. Verify that dataset and voice terms before commercial publication. The technical demo is not a substitute for that review. |
| MuseTalk 1.5 | Official Tencent Music Entertainment Lyra Lab repository | Lip sync | Preserve code/model notices and review licenses for all included or downloaded dependencies and face-analysis models. |
| Procedural sound worker | This repository | Original synthesized ambience, effects, and simple music | No external audio recording is bundled; preserve this repository's source license. |
| FFmpeg | Distribution package | Audio/video conversion, mixing, and delivery | The applicable FFmpeg license depends on the build and enabled codecs. Record the deployed build details. |

## Files that must be retained for a release-evidence bundle

For each real episode, retain:

1. `model-stack.json` and the exact model/checkpoint revisions.
2. Downloaded model cards and license files.
3. The approved series bible, character references, and visual prompts.
4. Seeds, workflow files, provider names, and job metadata.
5. The final `qc-report.json`.
6. Human review notes for accidental resemblance, logos, watermarks, unsafe content, and music similarity.
7. The exact FFmpeg build information and final export settings.

## Baseline status

The first real episode is cleared for **technical end-to-end testing**. It is not automatically cleared for advertising, resale, platform monetization, client delivery, or another commercial use until the voice dataset and every deployed model/runtime license have been reviewed for that use.
