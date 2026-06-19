# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Version numbers follow the pattern: `<spaCy-version>-<release-number>`

## [3.8.11-3] - 2026-06-19

### Fixed
- Worker-pool cascade crash on corpora containing a token whose surface form
  (FORM) is whitespace (e.g. a lone space). Such a token collapsed the
  tab-separated CoNLL-U line under `str.split()`, leaving 9 fields instead of
  10 and raising `IndexError` on the score column. The exception was uncaught
  and killed the whole streaming process, so korapxmltool's worker pool saw a
  broken pipe, re-queued the in-flight documents, and re-crashed on the same
  poisoned input until every worker died — observed as running threads dropping
  off one-by-one after tens of thousands of texts. `CoNLLUP_Token` now parses
  on the tab delimiter (preserving whitespace FORM columns), falls back to
  whitespace splitting for space-delimited input, and pads short lines to the
  10 CoNLL-U columns. As defense-in-depth, a parse/annotation failure for a
  single document is now logged and skipped while still echoing its
  `# eot`/`# eof` marker, so one bad document can no longer take down the run.

## [3.8.11-2] - 2026-06-10

### Fixed
- Streaming deadlock with korapxmltool on large corpora containing many small
  documents (e.g. Wikipedia article/discussion dumps), which manifested as
  near-idle CPU and a progress bar frozen at 0 for hours. The pipe now honors
  korapxmltool's `# eot`/`# eof` document-delimiter protocol: each document is
  annotated, emitted, and flushed immediately, so the worker pool can deliver
  results and release its bounded in-flight buffer slots. Previously `# eot`/
  `# eof` were swallowed as CoNLL-U comments, output was block-buffered with no
  flush, and nothing was delivered until the process exited at stdin EOF —
  which deadlocked once the in-flight buffer filled. Inputs without protocol
  markers (a CoNLL-U file piped in directly) are still processed in
  `SPACY_CHUNK_SIZE`-bounded blocks and now stream their output.

## [3.8.11-1] - 2025-11-30

### Added
- Initial release of conllu-spacy-docker
- Multi-language support for 70+ languages via spaCy models
- CoNLL-U input/output format support
- On-demand model fetching with caching in `/local/models`
- Optional GermaLemma integration for enhanced German lemmatization
- Morphological features extraction in CoNLL-U format
- Optional dependency parsing (HEAD/DEPREL columns)
- Command-line options: `-h`, `-m MODEL`, `-L`, `-V`, `-d`, `-g`
- Environment variables for configuration (batch size, chunk size, timeouts, etc.)
- Model preloading via `preload-models.sh` script
- Three Docker image variants:
  - Standard (662 MB) - with GermaLemma
  - Slim (490 MB) - without GermaLemma
  - With-models (1.22 GB) - includes pre-installed de_core_news_lg model
- Optimized Docker image using `COPY --chown` to avoid layer duplication
- CI/CD pipelines for GitLab and GitHub
- Progress indicators for model downloads
- Non-root user execution for security
- List available/installed models with `-L` flag
- Display version information with `-V` flag

### Features
- Based on spaCy 3.8.11
- Python 3.12.1
- GermaLemma 0.1.3 (optional)
- Multi-stage Docker build for size optimization
- Configurable dependency parsing with timeout protection
- Safe handling of long sentences
- Batch processing for performance
- Compatible with korapxmltool

[3.8.11-3]: https://github.com/KorAP/conllu-spacy-docker/releases/tag/3.8.11-3
[3.8.11-2]: https://github.com/KorAP/conllu-spacy-docker/releases/tag/3.8.11-2
[3.8.11-1]: https://github.com/KorAP/conllu-spacy-docker/releases/tag/3.8.11-1
