from collections import defaultdict, OrderedDict
import re

# CoNLL-U Format - https://universaldependencies.org/format.html


def get_token_type(type_str):
    if type_str =="CoNLL09_Token":
        return CoNLL09_Token
    elif type_str == "RNNTagger_Token":
        return RNNTagger_Token
    elif type_str == "CoNLLUP_Token":
        return CoNLLUP_Token
    elif type_str == "TigerNew_Token":
        return TigerNew_Token
    else:
        raise NotImplementedError(f"I don't know what to do with {type_str} token type!")


class TigerNew_Token():
    def __init__(self, raw_line, word_ix):
        info = raw_line.split() # [FORM, XPOS]
        self.info = info
        self.id = word_ix + 1 # 1-based ID as in the CoNLL file
        self.position = word_ix # 0-based position in sentence
        self.word = info[0]
        self.lemma = "_"
        self.pos_universal = "_"
        self.pos_tag = info[1]
        self.detail_tag = "_"
        self.head = "_"
        self.dep_tag = "_"
        self.blank = "_"
        self.auto_score = "_"
        
    def get_info(self):
        return [str(self.id), self.word, self.lemma, self.pos_universal, self.pos_tag, self.detail_tag,
                str(self.head), self.dep_tag, self.blank, self.auto_score]

    def get_conllU_line(self, separator="\t"):
        info = self.get_info()
        return separator.join(info)


class RNNTagger_Token():
    def __init__(self, raw_line, word_ix):
        info = raw_line.split() # [FORM, XPOS.FEATS, LEMMA]
        self.info = info
        self.id = word_ix + 1 # 1-based ID as in the CoNLL file
        self.position = word_ix # 0-based position in sentence
        self.word = info[0]
        self.lemma = info[2]
        self.pos_universal = "_"
        self.pos_tag, self.detail_tag = self._process_tag(info[1]) # 'NN.Gen.Sg.Fem'
        self.head = "_"
        self.dep_tag = "_"
        self.blank = "_"
        self.auto_score = "_"
        
    def _process_tag(self, tag):
        if tag == "_" or "." not in tag: return tag, "_"
        info = tag.split(".")
        return info[0], "|".join(info[1:])
        
    def get_info(self):
        return [str(self.id), self.word, self.lemma, self.pos_universal, self.pos_tag, self.detail_tag,
                str(self.head), self.dep_tag, self.blank, self.auto_score]

    def get_conllU_line(self, separator="\t"):
        info = self.get_info()
        return separator.join(info)


class CoNLLUP_Token():
    def __init__(self, raw_line, word_ix):
        info = raw_line.split()
        # print(info)
        # [ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC]
        # [11, Prügel, Prügel, NN, NN, _, _, _,	_, 1.000000]
        self.info = info
        self.id = info[0] # 1-based ID as in the CoNLL file
        self.position = word_ix # 0-based position in sentence
        self.word = info[1]
        self.lemma = info[2]
        self.pos_universal = info[3]
        self.pos_tag = self._process_tag(info[4]) # 'XPOS=NE|Case=Nom|Gender=Masc|Number=Sing' TODO: Reuse MorphInfo in the self.detail_tag
        self.detail_tag = info[5]
        self.head = info[6]
        self.dep_tag = info[7]
        self.blank = info[8] # ???
        self.auto_score = info[9]
        
    def _process_tag(self, tag):
        if tag == "_" or "|" not in tag: return tag # The XPOS=NE|Case=Nom... is only for Turku!
        info = tag.split("|")
        info = [x.split("=") for x in info]
        return info[0][1]
        
    def get_info(self):
        return [str(self.id), self.word, self.lemma, self.pos_universal, self.pos_tag, self.detail_tag,
                str(self.head), self.dep_tag, self.blank, self.auto_score]

    def get_conllU_line(self, separator="\t"):
        info = self.get_info()
        return separator.join(info)



class CoNLL09_Token():
    def __init__(self, raw_line, word_ix):
        info = raw_line.split()
        # print(info)
        # # ['1', 'Frau', 'Frau', 'Frau', 'NN', 'NN', '_', 'nom|sg|fem', '5', '5', 'CJ', 'CJ', '_', '_', 'AM-DIS', '_']
        self.info = info
        self.id = info[0] # 1-based ID as in the CoNLL file
        self.position = word_ix # 0-based position in sentence
        self.word = info[1]
        self.lemma = info[2]
        self.pos_universal = "_" # _convert_to_universal(self.pos_tag, self.lemma)
        self.pos_tag = info[4]
        self.head = info[8]
        self.dep_tag = info[10]
        self.detail_tag = "_"
        self.is_pred = True if info[12] == "Y" else False
        if self.is_pred:
            self.pred_sense = info[13].strip("[]")
            self.pred_sense_id = str(self.position) + "##" + self.pred_sense
        else:
            self.pred_sense = None
            self.pred_sense_id = ""
        if len(info) > 14:
            self.labels = info[14:]
        else:
            self.labels = []

    def get_conllU_line(self, separator="\t"):
        # We want: [ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC]
        tok_id = str(self.id) #.split("_")[0]
        conllUinfo = [tok_id, self.word, self.lemma, self.pos_universal, self.pos_tag, self.detail_tag, self.head, self.dep_tag, "_", "_"]
        return separator.join(conllUinfo)

    def get_conll09_line(self, delim="\t"):
        # We want:
        # 1 Frau Frau Frau NN NN _ nom|sg|fem 5 5 CJ CJ _ _ AM-DIS _
        # 10	fall	fall	fall	VB	VB	_	_	8	8	VC	VC	Y	fall.01	_	_	_	_	_
        is_pred_str = "Y" if self.is_pred else "_"
        sense_str = self.pred_sense if self.is_pred else "_"
        info = [self.id, self.word, self.lemma, self.lemma, self.pos_tag, self.pos_tag, "_", self.detail_tag,
                self.head, self.head, self.dep_tag, self.dep_tag, is_pred_str, sense_str] + self.labels
        return delim.join(info)



################################# GETTING SENTENCE ANNOTATIONS ####################################
class AnnotatedSentence():
    def __init__(self):
        self.metadata = []
        self.tokens = []

    def get_words(self):
        return [tok.word for tok in self.tokens]

    def get_sentence(self):
        return " ".join([tok.word for tok in self.tokens])

    def get_pos_tags(self, universal=False):
        if universal:
            return [tok.pos_universal for tok in self.tokens]
        else:
            return [tok.pos_tag for tok in self.tokens]


def get_annotation(raw_lines, raw_meta, token_class):
    ann = AnnotatedSentence()
    ann.metadata = [m.strip("\n") for m in raw_meta]
    # Annotate the predicates and senses
    real_index = 0
    for i, line in enumerate(raw_lines):
        tok = token_class(line, real_index)
        ann.tokens.append(tok)
        real_index += 1
    return ann


def read_conll(line_generator, chunk_size, token_class=CoNLLUP_Token, comment_str="###C:", our_foundry="spacy"):
    n_sents = 0
    annotated_sentences, buffer_meta, buffer_lst = [], [], []
    for i, line in enumerate(line_generator):
        if line.startswith(comment_str):
            line = re.sub(r'(foundry\s*=\s*).*', r"\1" + our_foundry, line)
            line = re.sub(r'(filename\s*=\s* .[^/]*/[^/]+/[^/]+/).*', r"\1" + our_foundry + "/morpho.xml", line)
            buffer_meta.append(line)
            continue
        if len(line.split()) > 0:
            buffer_lst.append(line)
        else:
            ann = get_annotation(buffer_lst, buffer_meta, token_class)
            n_sents += 1
            buffer_lst, buffer_meta = [], []
            annotated_sentences.append(ann)
        if chunk_size > 0 and n_sents == chunk_size: break
    # logger.info("Read {} Sentences!".format(n_sents))
    return annotated_sentences, n_sents

    
def read_conll_generator(filepath, token_class=CoNLLUP_Token, sent_sep=None, comment_str="###C:"):
    buffer_meta, buffer_lst = [], []
    sentence_finished = False
    with open(filepath) as f:
        for i, line in enumerate(f.readlines()):
            if sent_sep and sent_sep in line: sentence_finished = True
            if line.startswith(comment_str):
                continue
            if len(line.split()) > 0 and not sentence_finished:
                buffer_lst.append(line)
            else:
                ann = get_annotation(buffer_lst, buffer_meta, token_class)
                buffer_lst, buffer_meta = [], []
                sentence_finished = False
                yield ann