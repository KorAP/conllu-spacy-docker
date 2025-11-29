from sys import stdin
import argparse, os
import spacy
from spacy.tokens import Doc
import logging, sys, time, signal
from lib.CoNLL_Annotation import get_token_type
import my_utils.file_utils as fu

# Try to import GermaLemma, but make it optional
try:
    from germalemma import GermaLemma
    GERMALEMMA_AVAILABLE = True
except ImportError:
    GERMALEMMA_AVAILABLE = False
    GermaLemma = None

# Dependency parsing safety limits
DEFAULT_PARSE_TIMEOUT = 0.5  # seconds per sentence
DEFAULT_MAX_SENTENCE_LENGTH = 500  # tokens

class TimeoutException(Exception):
	pass

def timeout_handler(signum, frame):
	raise TimeoutException("Dependency parsing timeout")

def safe_dependency_parse(spacy_model, text, timeout=DEFAULT_PARSE_TIMEOUT, max_length=DEFAULT_MAX_SENTENCE_LENGTH):
	"""
	Safely parse a sentence with timeout and length limits.
	
	Args:
		spacy_model: Loaded spaCy model
		text: Text to parse
		timeout: Maximum seconds to wait for parsing
		max_length: Maximum sentence length in tokens
		
	Returns:
		tuple: (spacy_doc, success, warning_message)
	"""
	# Check sentence length
	if len(text.split()) > max_length:
		# Process without dependency parsing for long sentences
		disabled_components = ["ner", "parser"]
		doc = spacy_model(text, disable=disabled_components)
		return doc, False, f"Sentence too long ({len(text.split())} tokens > {max_length}), dependency parsing skipped"
	
	# Set up timeout
	old_handler = signal.signal(signal.SIGALRM, timeout_handler)
	signal.setitimer(signal.ITIMER_REAL, timeout)
	
	try:
		doc = spacy_model(text)
		signal.setitimer(signal.ITIMER_REAL, 0)  # Cancel alarm
		signal.signal(signal.SIGALRM, old_handler)
		return doc, True, None
	except TimeoutException:
		signal.setitimer(signal.ITIMER_REAL, 0)  # Cancel alarm
		signal.signal(signal.SIGALRM, old_handler)
		# Retry without dependency parsing
		disabled_components = ["ner", "parser"]
		doc = spacy_model(text, disable=disabled_components)
		return doc, False, f"Dependency parsing timeout after {timeout}s, processed without dependencies"
	except Exception as e:
		signal.setitimer(signal.ITIMER_REAL, 0)  # Cancel alarm
		signal.signal(signal.SIGALRM, old_handler)
		# Retry without dependency parsing
		disabled_components = ["ner", "parser"]
		doc = spacy_model(text, disable=disabled_components)
		return doc, False, f"Dependency parsing error: {str(e)}, processed without dependencies"

def format_morphological_features(token):
	"""
	Extract and format morphological features from a spaCy token for CoNLL-U output.
	
	Args:
		token: spaCy token object
		
	Returns:
		str: Formatted morphological features string for CoNLL-U 5th column
			 Returns "_" if no features are available
	"""
	if not hasattr(token, 'morph') or not token.morph:
		return "_"
	
	morph_dict = token.morph.to_dict()
	if not morph_dict:
		return "_"
	
	# Format as CoNLL-U format: Feature=Value|Feature2=Value2
	features = []
	for feature, value in sorted(morph_dict.items()):
		features.append(f"{feature}={value}")
	
	return "|".join(features)


def format_dependency_relations(doc):
	"""
	Extract and format dependency relations from a spaCy doc for CoNLL-U output.
	
	Args:
		doc: spaCy Doc object
		
	Returns:
		list: List of tuples (head_id, deprel) for each token
	"""
	dependencies = []
	for i, token in enumerate(doc):
		# HEAD column: 1-based index of the head token (0 for root)
		if token.dep_ == "ROOT":
			head_id = 0
		else:
			# Find the 1-based index of the head token
			head_id = None
			for j, potential_head in enumerate(doc):
				if potential_head == token.head:
					head_id = j + 1
					break
			if head_id is None:
				head_id = 0  # Fallback to root if head not found
		
		# DEPREL column: dependency relation
		deprel = token.dep_ if token.dep_ else "_"
		
		dependencies.append((head_id, deprel))
	
	return dependencies


class WhitespaceTokenizer(object):
	def __init__(self, vocab):
		self.vocab = vocab

	def __call__(self, text):
		words = text.split(' ')
		# Filter out empty strings to avoid spaCy errors
		words = [w for w in words if w]
		# Handle edge case of empty input - use a placeholder token
		if not words:
			words = ['_EMPTY_']
		# All tokens 'own' a subsequent space character in this tokenizer
		spaces = [True] * len(words)
		return Doc(self.vocab, words=words, spaces=spaces)


def get_conll_str(anno_obj, spacy_doc, use_germalemma, use_dependencies):
	#  First lines are comments. (metadata)
	conll_lines = anno_obj.metadata # Then we want: [ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC]
	
	# Get dependency relations if enabled
	dependencies = format_dependency_relations(spacy_doc) if use_dependencies == "True" else None
	
	for ix, token in enumerate(spacy_doc):
		morph_features = format_morphological_features(token)
		
		# Get HEAD and DEPREL columns
		if dependencies:
			head_id, deprel = dependencies[ix]
		else:
			head_id, deprel = "_", "_"
		
		if use_germalemma == "True":
			content = (str(ix+1), token.text, find_germalemma(token.text, token.tag_, token.lemma_), token.pos_, token.tag_, morph_features, str(head_id), deprel, "_", "_")
		else:
			content = (str(ix+1), token.text, token.lemma_, token.pos_, token.tag_, morph_features, str(head_id), deprel, "_", "_") # Pure SpaCy!
		conll_lines.append("\t".join(content))
	return "\n".join(conll_lines)

	
def find_germalemma(word, pos, spacy_lemma):
	simplify_pos = {"ADJA":"ADJ", "ADJD":"ADJ",
					"NA":"N", "NE":"N", "NN":"N",
					"ADV":"ADV", "PAV":"ADV", "PROAV":"ADV", "PAVREL":"ADV", "PWAV":"ADV", "PWAVREL":"ADV",
					"VAFIN":"V", "VAIMP":"V", "VAINF":"V", "VAPP":"V", "VMFIN":"V", "VMINF":"V",
					"VMPP":"V", "VVFIN":"V", "VVIMP":"V", "VVINF":"V", "VVIZU":"V","VVPP":"V"
				}
	# simplify_pos = {"VERB": "V", "ADV": "ADV", "ADJ": "ADJ", "NOUN":"N", "PROPN": "N"}
	try:
		return lemmatizer.find_lemma(word, simplify_pos.get(pos, "UNK"))
	except:
		return spacy_lemma


if __name__ == "__main__":
	"""
		--- Example Real Data TEST  ---
		
		cat /export/netapp/kupietz/N-GRAMM-STUDIE/conllu/zca18.conllu | python systems/parse_spacy_pipe.py \
			--corpus_name DeReKo_zca18 --comment_str "#" > output_zca18.conll
	"""
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-n", "--corpus_name", help="Corpus Name", default="Corpus")
	parser.add_argument("-sm", "--spacy_model", help="Spacy model containing the pipeline to tag", default="de_core_news_lg")
	parser.add_argument("-gtt", "--gld_token_type", help="CoNLL Format of the Gold Data", default="CoNLLUP_Token")
	parser.add_argument("-ugl", "--use_germalemma", help="Use Germalemma lemmatizer on top of SpaCy", default="True")
	parser.add_argument("-udp", "--use_dependencies", help="Include dependency parsing (adds HEAD/DEPREL columns, set to False for faster processing)", default="True")
	parser.add_argument("-c", "--comment_str", help="CoNLL Format of comentaries inside the file", default="#")
	args = parser.parse_args()
	
	file_has_next, chunk_ix = True, 0
	CHUNK_SIZE = int(os.getenv("SPACY_CHUNK_SIZE", "20000"))
	SPACY_BATCH = int(os.getenv("SPACY_BATCH_SIZE", "2000"))
	SPACY_PROC = int(os.getenv("SPACY_N_PROCESS", "1"))
	
	# =====================================================================================
	#                    LOGGING INFO ...
	# =====================================================================================
	logger = logging.getLogger(__name__)
	console_hdlr = logging.StreamHandler(sys.stderr)
	file_hdlr = logging.FileHandler(filename=f"logs/Parse_{args.corpus_name}.SpaCy.log")
	
	# Custom format without module name
	formatter = logging.Formatter('%(levelname)s: %(message)s')
	console_hdlr.setFormatter(formatter)
	file_hdlr.setFormatter(formatter)
	
	logging.basicConfig(level=logging.INFO, handlers=[console_hdlr, file_hdlr])
	
	# Override with environment variables if set (useful for Docker)
	import os
	if os.getenv("SPACY_USE_DEPENDENCIES") is not None:
		args.use_dependencies = os.getenv("SPACY_USE_DEPENDENCIES", "True")
		logger.info(f"Using SPACY_USE_DEPENDENCIES environment variable: {args.use_dependencies}")
	
	if os.getenv("SPACY_USE_GERMALEMMA") is not None:
		args.use_germalemma = os.getenv("SPACY_USE_GERMALEMMA", "True")
		logger.info(f"Using SPACY_USE_GERMALEMMA environment variable: {args.use_germalemma}")
	
	logger.info(f"Chunking {args.corpus_name} Corpus in chunks of {CHUNK_SIZE} Sentences")
	logger.info(f"Processing configuration: batch_size={SPACY_BATCH}, n_process={SPACY_PROC}")
	
	# =====================================================================================
	#                    POS TAG DOCUMENTS
	# =====================================================================================
	# Configure which components to disable based on dependency parsing option
	disabled_components = ["ner"]
	if args.use_dependencies != "True":
		disabled_components.append("parser")
		logger.info("Dependency parsing disabled for faster processing")
	else:
		logger.info("Dependency parsing enabled (slower but includes HEAD/DEPREL)")
	
	spacy_de = spacy.load(args.spacy_model, disable=disabled_components)
	spacy_de.tokenizer = WhitespaceTokenizer(spacy_de.vocab) # We won't re-tokenize to respect how the source CoNLL are tokenized!

	# Increase max_length to handle very long sentences (especially when parser is disabled)
	spacy_de.max_length = 10000000  # 10M characters

	# Initialize GermaLemma if available and requested
	lemmatizer = None
	if args.use_germalemma == "True":
		if GERMALEMMA_AVAILABLE:
			lemmatizer = GermaLemma()
		else:
			logger.warning("GermaLemma requested but not available. Using spaCy lemmatizer instead.")
			args.use_germalemma = "False"
	
	# Log version information
	logger.info(f"spaCy version: {spacy.__version__}")
	logger.info(f"spaCy model: {args.spacy_model}")
	logger.info(f"spaCy model version: {spacy_de.meta.get('version', 'unknown')}")
	if GERMALEMMA_AVAILABLE:
		try:
			import germalemma
			logger.info(f"GermaLemma version: {germalemma.__version__}")
		except AttributeError:
			logger.info("GermaLemma version: unknown (no __version__ attribute)")
	else:
		logger.info("GermaLemma: not installed")
	
	# Parse timeout and sentence length limits from environment variables
	parse_timeout = float(os.getenv("SPACY_PARSE_TIMEOUT", str(DEFAULT_PARSE_TIMEOUT)))
	max_sentence_length = int(os.getenv("SPACY_MAX_SENTENCE_LENGTH", str(DEFAULT_MAX_SENTENCE_LENGTH)))
	
	logger.info(f"Dependency parsing limits: timeout={parse_timeout}s, max_length={max_sentence_length} tokens")
	
	start = time.time()
	total_processed_sents = 0
	dependency_warnings = 0
	
	while file_has_next:
		annos, file_has_next = fu.get_file_annos_chunk(stdin, chunk_size=CHUNK_SIZE, token_class=get_token_type(args.gld_token_type), comment_str=args.comment_str, our_foundry="spacy")
		if len(annos) == 0: break
		total_processed_sents += len(annos)
		
		# Calculate progress statistics
		elapsed_time = time.time() - start
		sents_per_sec = total_processed_sents / elapsed_time if elapsed_time > 0 else 0
		current_time = time.strftime("%Y-%m-%d %H:%M:%S")
		
		logger.info(f"{current_time} | Processed: {total_processed_sents} sentences | Elapsed: {elapsed_time:.1f}s | Speed: {sents_per_sec:.1f} sents/sec")
		
		sents = [a.get_sentence() for a in annos]
		
		# Process sentences individually when dependency parsing is enabled for timeout protection
		if args.use_dependencies == "True":
			for ix, sent in enumerate(sents):
				doc, dependency_success, warning = safe_dependency_parse(
					spacy_de, sent, timeout=parse_timeout, max_length=max_sentence_length
				)
				if warning:
					dependency_warnings += 1
					logger.warning(f"Sentence {total_processed_sents - len(sents) + ix + 1}: {warning}")
				
				# Override use_dependencies based on actual parsing success
				actual_use_dependencies = "True" if dependency_success else "False"
				conll_str = get_conll_str(annos[ix], doc, use_germalemma=args.use_germalemma, use_dependencies=actual_use_dependencies)
				print(conll_str+ "\n")
		else:
			# Use batch processing for faster processing when dependencies are disabled
			# Use n_process=1 to avoid multiprocessing deadlocks and memory issues with large files
			try:
				for ix, doc in enumerate(spacy_de.pipe(sents, batch_size=SPACY_BATCH, n_process=1)):
					conll_str = get_conll_str(annos[ix], doc, use_germalemma=args.use_germalemma, use_dependencies=args.use_dependencies)
					print(conll_str+ "\n")
			except Exception as e:
				logger.error(f"Batch processing failed: {str(e)}")
				logger.info("Falling back to individual sentence processing...")
				# Fallback: process sentences individually
				for ix, sent in enumerate(sents):
					try:
						doc = spacy_de(sent)
						conll_str = get_conll_str(annos[ix], doc, use_germalemma=args.use_germalemma, use_dependencies=args.use_dependencies)
						print(conll_str+ "\n")
					except Exception as sent_error:
						logger.error(f"Failed to process sentence {total_processed_sents - len(sents) + ix + 1}: {str(sent_error)}")
						logger.error(f"Sentence preview: {sent[:100]}...")
						# Output a placeholder to maintain alignment
						conll_str = get_conll_str(annos[ix], spacy_de("ERROR"), use_germalemma=args.use_germalemma, use_dependencies=args.use_dependencies)
						print(conll_str+ "\n")
			
	end = time.time()
	total_time = end - start
	final_sents_per_sec = total_processed_sents / total_time if total_time > 0 else 0
	
	logger.info(f"=== Processing Complete ===")
	logger.info(f"Total sentences: {total_processed_sents}")
	logger.info(f"Total time: {total_time:.2f}s")
	logger.info(f"Average speed: {final_sents_per_sec:.1f} sents/sec")
	
	if dependency_warnings > 0:
		logger.info(f"Dependency parsing warnings: {dependency_warnings} sentences processed without dependencies")
			