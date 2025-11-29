.PHONY: build build-with-models preload-models run test clean

build:
	docker build -t korap/conllu-spacy:latest .

build-with-models:
	docker build -f Dockerfile.with-models -t korap/conllu-spacy:with-models .

preload-models:
	@echo "Preloading default model (de_core_news_lg) to ./models..."
	./preload-models.sh

preload-models-all:
	@echo "Preloading all models to ./models..."
	./preload-models.sh de_core_news_lg ./models
	./preload-models.sh de_core_news_md ./models
	./preload-models.sh de_core_news_sm ./models

run:
	docker run --rm -i korap/conllu-spacy:latest

test:
	@echo "Testing with sample input..."
	@echo "Not implemented yet - add test input file"

clean:
	docker rmi korap/conllu-spacy:latest
