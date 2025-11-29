# spaCy Docker Image with CoNLL-U Support

Docker image for **spaCy** POS tagging, lemmatization and dependency parsing with support for input and output in [CoNLL-U format](https://universaldependencies.org/format.html).

This is a slim, focused implementation extracted from [sota-pos-lemmatizers](https://korap.ids-mannheim.de/gerrit/plugins/gitiles/KorAP/sota-pos-lemmatizers), originally developed by José Angel Daza(@angel-daza), following the same pattern as [conllu-treetagger-docker](https://github.com/KorAP/conllu-treetagger-docker).

## Features

- **Multi-language support**: Works with any spaCy model for 70+ languages
- **CoNLL-U input/output**: Reads and writes CoNLL-U format
- **On-demand model fetching**: Models are downloaded on first run and cached in `/local/models`
- **GermaLemma integration**: Enhanced lemmatization for German (optional, German models only)
- **Morphological features**: Extracts and formats morphological features in CoNLL-U format
- **Dependency parsing**: Optional dependency relations (HEAD/DEPREL columns)
- **Flexible configuration**: Environment variables for batch size, chunk size, timeouts, etc.

## Installation

### From source

```shell
git clone https://github.com/KorAP/conllu-spacy-tagger-docker.git
cd conllu-spacy-tagger-docker
docker build -t korap/conllu-spacy .
```

## Usage

### Basic usage

```shell
# Default: German model with dependency parsing and GermaLemma
docker run --rm -i korap/conllu-spacy < input.conllu > output.conllu
```

### Faster processing without dependency parsing

```shell
# Disable dependency parsing for faster processing
docker run --rm -i korap/conllu-spacy -d < input.conllu > output.conllu
```

### Using different language models

```shell
# Use a smaller German model
docker run --rm -i korap/conllu-spacy -m de_core_news_sm < input.conllu > output.conllu

# Use French model
docker run --rm -i korap/conllu-spacy -m fr_core_news_lg < input.conllu > output.conllu

# Use English model (disable GermaLemma for non-German)
docker run --rm -i korap/conllu-spacy -m en_core_web_lg -g < input.conllu > output.conllu
```

### Persisting Models

To avoid downloading the language model on every run, mount a local directory to `/local/models`:

```shell
docker run --rm -i -v /path/to/local/models:/local/models korap/conllu-spacy < input.conllu > output.conllu
```

The first run will download the model to `/path/to/local/models/`, and subsequent runs will reuse it.

### Preloading Models

There are several ways to preload models before running the container:

#### Option 1: Using the preload script (recommended)

```shell
# Preload the default model (de_core_news_lg)
./preload-models.sh

# Preload a specific model
./preload-models.sh de_core_news_sm

# Preload to a custom directory
./preload-models.sh de_core_news_lg /path/to/models

# Then run with the preloaded models
docker run --rm -i -v ./models:/local/models korap/conllu-spacy < input.conllu
```

#### Option 2: Build image with models included

```shell
# Build an image with models pre-installed
docker build -f Dockerfile.with-models -t korap/conllu-spacy:with-models .

# Run without needing to mount volumes
docker run --rm -i korap/conllu-spacy:with-models < input.conllu > output.conllu
```

Edit `Dockerfile.with-models` to include additional models (sm, md) by uncommenting the relevant lines.

#### Option 3: Manual download

```shell
# Create models directory
mkdir -p ./models

# Download using a temporary container
docker run --rm -v ./models:/models python:3.12-slim bash -c "
  pip install -q spacy &&
  python -m spacy download de_core_news_lg &&
  python -c 'import spacy, shutil, site;
  shutil.copytree(site.getsitepackages()[0] + \"/de_core_news_lg\", \"/models/de_core_news_lg\")'
"

# Use the preloaded model
docker run --rm -i -v ./models:/local/models korap/conllu-spacy < input.conllu
```

### Running with korapxmltool

`korapxmltool`, which includes `korapxml2conllu` as a shortcut, can be downloaded from [https://github.com/KorAP/korapxmltool](https://github.com/KorAP/korapxmltool).

```shell
korapxml2conllu goe.zip | docker run --rm -i korap/conllu-spacy
```

#### Generate a spaCy-tagged KorAP XML zip directly

```shell
korapxmltool -A "docker run --rm -i korap/conllu-spacy" -t zip goe.zip
```

### Command-line Options

```
Usage: docker run --rm -i korap/conllu-spacy [OPTIONS]

Options:
  -h            Display help message
  -m MODEL      Specify spaCy model (default: de_core_news_lg)
  -L            List available/installed models
  -d            Disable dependency parsing (faster processing)
  -g            Disable GermaLemma (use spaCy lemmatizer only)
```

### Environment Variables

You can customize processing behavior with environment variables:

```shell
docker run --rm -i \
  -e SPACY_USE_DEPENDENCIES="False" \
  -e SPACY_USE_GERMALEMMA="True" \
  -e SPACY_CHUNK_SIZE="10000" \
  -e SPACY_BATCH_SIZE="1000" \
  -e SPACY_N_PROCESS="1" \
  -e SPACY_PARSE_TIMEOUT="30" \
  -e SPACY_MAX_SENTENCE_LENGTH="500" \
  korap/conllu-spacy < input.conllu > output.conllu
```

**Available environment variables:**

- `SPACY_USE_DEPENDENCIES`: Enable/disable dependency parsing (default: "True")
- `SPACY_USE_GERMALEMMA`: Enable/disable GermaLemma (default: "True")
- `SPACY_CHUNK_SIZE`: Number of sentences to process per chunk (default: 20000)
- `SPACY_BATCH_SIZE`: Batch size for spaCy processing (default: 2000)
- `SPACY_N_PROCESS`: Number of processes (default: 10)
- `SPACY_PARSE_TIMEOUT`: Timeout for dependency parsing per sentence in seconds (default: 30)
- `SPACY_MAX_SENTENCE_LENGTH`: Maximum sentence length for dependency parsing in tokens (default: 500)

### Examples

```shell
# Fast processing: disable dependency parsing
docker run --rm -i korap/conllu-spacy -d < input.conllu > output.conllu

# Use spaCy lemmatizer only (without GermaLemma)
docker run --rm -i korap/conllu-spacy -g < input.conllu > output.conllu

# Smaller model for faster download
docker run --rm -i korap/conllu-spacy -m de_core_news_sm < input.conllu > output.conllu

# Persistent model storage
docker run --rm -i -v ./models:/local/models korap/conllu-spacy < input.conllu > output.conllu
```

### Miscellaneous commands

List installed models:

```shell
docker run --rm -i korap/conllu-spacy -L
```

Open a shell within the container:

```shell
docker run --rm -it --entrypoint /bin/bash korap/conllu-spacy
```

## Supported Languages and Models

Any spaCy model can be specified with the `-m` option. Models will be downloaded automatically on first use.

spaCy provides trained models for **70+ languages**. See [spaCy Models](https://spacy.io/models) for the complete list.

### Example: German models (default)
- `de_core_news_lg` (default, 560MB) - Large model, best accuracy
- `de_core_news_md` (100MB) - Medium model, balanced
- `de_core_news_sm` (15MB) - Small model, fastest

### Example: French models
```shell
# Use French small model
docker run --rm -i -v ./models:/local/models korap/conllu-spacy -m fr_core_news_sm < input.conllu
```
- `fr_core_news_lg` (560MB) - Large French model
- `fr_core_news_md` (100MB) - Medium French model
- `fr_core_news_sm` (15MB) - Small French model

### Example: English models
```shell
# Use English model
docker run --rm -i -v ./models:/local/models korap/conllu-spacy -m en_core_web_lg < input.conllu
```
- `en_core_web_lg` (560MB) - Large English model
- `en_core_web_md` (100MB) - Medium English model
- `en_core_web_sm` (15MB) - Small English model

### Other supported languages

Models are available for: Catalan, Chinese, Croatian, Danish, Dutch, Finnish, Greek, Italian, Japanese, Korean, Lithuanian, Macedonian, Norwegian, Polish, Portuguese, Romanian, Russian, Spanish, Swedish, Ukrainian, and many more.

**Note**: GermaLemma integration only works with German models. For other languages, the standard spaCy lemmatizer is used (with `-g` flag to disable GermaLemma).

## Performance

From the sota-pos-lemmatizers benchmarks on the TIGER corpus (50,472 sentences):

| Configuration                  | Lemma Acc | POS Acc | POS F1 | sents/sec |
|--------------------------------|-----------|---------|--------|-----------|
| spaCy + GermaLemma             | **90.98** | **99.07**| **95.84** | **1,230** |
| spaCy (without GermaLemma)     | 85.33     | 99.07   | 95.84  | 1,577     |

**Note**: Disabling dependency parsing (`-d` flag) significantly improves processing speed while maintaining POS tagging and lemmatization quality.

## Architecture

The project consists of:

- **Dockerfile**: Multi-stage build for optimized image size
- **docker-entrypoint.sh**: Entry point script that handles model fetching and CLI argument parsing
- **systems/parse_spacy_pipe.py**: Main spaCy processing pipeline
- **lib/CoNLL_Annotation.py**: CoNLL-U format parsing and token classes
- **my_utils/file_utils.py**: File handling utilities for chunked processing

## Credits

Based on the [sota-pos-lemmatizers](https://korap.ids-mannheim.de/gerrit/plugins/gitiles/KorAP/sota-pos-lemmatizers) evaluation project, originally by [José Angel Daza](https://github.com/angel-daza) and [Marc Kupietz](https://github.com/kupietz), with contributions by [Rebecca Wilm](https://github.com/rebecca-wilm), follows the pattern established by [conllu-treetagger-docker](https://github.com/KorAP/conllu-treetagger-docker).

- **spaCy**: [https://spacy.io/](https://spacy.io/)
- **GermaLemma**: [https://github.com/WZBSocialScienceCenter/germalemma](https://github.com/WZBSocialScienceCenter/germalemma)

## License

See the licenses of the individual components:
- spaCy: MIT License
- GermaLemma: Apache 2.0 License
