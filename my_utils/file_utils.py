import requests, logging, json
import subprocess, time
import glob, logging
import os.path, sys
from lib.CoNLL_Annotation import read_conll, read_conll_generator

logger = logging.getLogger(__name__)


def list_to_file(my_list, out_path):
    with open(out_path, "w") as out:
        for item_str in my_list:
            out.write(f"{item_str}\n")

def counter_to_file(my_counter, out_path):
    with open(out_path, "w") as out:
        for item, count in my_counter:
            item_str = "\t".join(item)
            out.write(f"{item_str}\t{count}\n")

def dict_to_file(my_dict, out_path):
    with open(out_path, "w", encoding='utf8') as out:
        json.dump(my_dict, fp=out, ensure_ascii=False)


def file_to_dict(file_path):
    d = {}
    with open(file_path) as f:
        d = json.load(f)
    return d  


def write_conll_file(conll_objs, out_path):
    with open(out_path, "w", encoding='utf8') as out:
        for obj in conll_objs:
            for tok in obj.tokens:
                out.write(tok.get_conllU_line()+"\n")
            out.write("\n")

def file_generator(file_path):
    with open(file_path, "r") as data_file:
        logger.info("Reading instances from lines in file at: %s", file_path)
        for line in data_file:
            if not line: continue
            yield line


def get_file_annos_chunk(line_generator, chunk_size, token_class, comment_str="###C:", our_foundry="spacy"):
    file_has_next = True
    chunk, n_sents = read_conll(line_generator, chunk_size, token_class, comment_str=comment_str, our_foundry=our_foundry)
    if n_sents == 0: file_has_next = False
    sents, gld, meta = [], [], []
    return chunk, file_has_next


def get_file_text_chunk(line_generator, chunk_size, token_class, comment_str="###C:"):
    """ Same as get_file_annos_chunk but directly get (text, labels) pairs"""
    file_has_next = True
    chunk, n_sents = read_conll(line_generator, chunk_size, token_class, comment_str=comment_str)
    if n_sents == 0: file_has_next = False
    sents, gld, meta = [], [], []
    for anno in chunk:
        if len(anno.metadata) > 0: meta.append("\n".join(anno.metadata))
        sents.append(anno.get_sentence())
        gld.append(anno.get_pos_tags())
    return sents, gld, file_has_next


def get_file_chunk(line_generator, chunk_size, token_class, comment_str="###C:"):
    file_has_next = True
    chunk, n_sents = read_conll(line_generator, chunk_size, token_class, comment_str=comment_str)
    if n_sents < chunk_size: file_has_next = False
    raw_text = ""
    for anno in chunk:
        if len(anno.metadata) > 0: 
            raw_text += "\n".join(anno.metadata) + "\n"
        else:
            raw_text += "\n"
        for tok in anno.tokens:
            raw_text += tok.get_conllU_line() + "\n"
        raw_text += "\n"
    return raw_text, file_has_next, n_sents


def turku_parse_file(raw_text, filename, chunk_ix):
    out_file_str = f"{filename}.parsed.{chunk_ix}.conllu"
    # For each file make a request to obtain the parse back
    logger.info(f"Sending Request {chunk_ix} to Parser Server...")
    response = requests.post("http://localhost:7689/", data=raw_text.encode('utf-8'))
    response_to_file(response.text, out_file_str)



def response_to_file(response_str, fname):
    fout = open(fname, "w")
    fout.write(response_str)
    fout.close()


def expand_file(f, substitute_comment=False):
    # Expand the .gz file
    fname = f[:-3]
    if not os.path.isfile(fname): 
        p = subprocess.call(f"gunzip -c {f} > {fname}", shell=True)
        if p == 0:
            logger.info("Successfully uncompressed file")
        else:
            logger.info(f"Couldn't expand file {f}")
            raise Exception
    else:
        logger.info(f"File {fname} is already uncompressed. Skipping this step...")
    
    # Substitute the Commentary Lines on the Expanded file
    if substitute_comment:
        fixed_filename = f"{fname}.fixed"
        p = subprocess.call(f"sed 's/^# /###C: /g' {fname}", shell=True, stdout=open(fixed_filename, "w")) # stdout=subprocess.PIPE
        if p == 0:
            logger.info("Successfully fixed comments on file")
        else:
            logger.info(f"Something went wrong when substituting commentaries")
            raise Exception    
        return fixed_filename
    else:
        return fname
