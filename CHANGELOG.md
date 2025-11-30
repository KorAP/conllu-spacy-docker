# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Version numbers follow the pattern: `<spaCy-version>-<release-number>`

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

[3.8.11-1]: https://github.com/KorAP/conllu-spacy-docker/releases/tag/3.8.11-1
