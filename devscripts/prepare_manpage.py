from __future__ import unicode_literals

import io
import os.path
import re
import scm

ROOT_DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(ROOT_DIR_PATH, "README.md")

with io.open(README_PATH, encoding="utf-8") as FILE:
    README_ORIG = FILE.read()

if README_ORIG:
    README = "=pod\n\n=encoding utf8\n\n# NAME\n\n" + README_ORIG + "\n\n=cut\n"
else:
    README = ""

def identity(x): return x

def _compose(f, g): return lambda x: f(g(x))

def compose(*tuple_of_func):
    lst_of_func = scm.tuple_to_lst(tuple_of_func)
    return scm.fold(_compose, identity, scm.reverse(lst_of_func))

def flatten(lst):
    """flatten an arbitrarily deep nested lst into a single lst"""
    if lst is scm.nil:
        return scm.nil
    elif not scm.is_list(lst):
        return scm.list(lst)
    else:
        return scm.append(flatten(scm.car(lst)),
                          flatten(scm.cdr(lst)))

def list_subtract(lst1, lst2):
    return scm.lset_difference(lambda x, y: x == y, lst1, lst2)

def non_nil_take_while(pred, lst):
    return scm.take_while(pred,
                          scm.drop_while(lambda x: not pred(x),
                                         lst))

def string_join(lst_of_string, delimiter):
    list_of_string = scm.lst_to_list(lst_of_string)
    return delimiter.join(list_of_string)

def is_not_empty_string(s_exp):
    return not scm.is_string(s_exp) or bool(s_exp)

def regex_split(pattern, string, flags=0):
    """split string into lst using pattern"""
    return scm.list_to_lst(re.split(pattern, string, 0, flags))

def remove_table_of_content(string):
    pattern = r"^-[ \t]+\[[- \tA-Z]+\]\(#[-a-z]+\)[ \t]*$"
    return re.sub(pattern, r"", string, 0, re.MULTILINE)

def make_lexer(split_pattern, sub_pattern , exp_type, flags=0):
    """
    Lexer is a procedure which does the following:

    1. Split string into lst using split_pattern
    2. Transform matching string in lst using sub_pattern
    and attach exp_type to it, forming an expression

    The output is a lst of tokens consisting of string and expression

    """
    def attach_exp_type_to_matching_substring(string):
        if re.search(split_pattern, string, flags):
            return scm.list(exp_type,
                            re.sub(sub_pattern, r"\1", string, 1, flags))
        else:
            return string
    return lambda string: scm.map(attach_exp_type_to_matching_substring,
                                  regex_split(split_pattern, string, flags))

def make_parser(exp_type, post_proc):
    """
    Parser is a procedure which takes the output of a lexer as input
    and does the following:

    1. Group exp_type expression and the string after it
    2. Apply post_proc to the string after exp_type expression

    The output is a tree-like structure

    """
    def is_exp(lst): return scm.is_list(scm.car(lst))
    def extract_exp(lst): return scm.car(lst)
    def extract_string_after_exp(lst): return scm.cadr(lst)
    def extract_rest(lst): return scm.cddr(lst)
    def parse_loop(lst, accum):
        if lst is scm.nil:
            return accum
        elif is_exp(lst):
            return parse_loop(extract_rest(lst),
                              scm.cons(scm.list(extract_exp(lst),
                                                post_proc(extract_string_after_exp(lst))),
                                       accum))
        else:
            return parse_loop(scm.cdr(lst),
                              scm.cons(post_proc(scm.car(lst)),
                                       accum))
    return lambda lst: scm.reverse(parse_loop(lst, scm.nil))

def make_front_end(post_proc, split_pattern, sub_pattern, exp_type, flags=0):
    """compose parser and lexer to create a front end"""
    return compose(make_parser(exp_type, post_proc),
                   make_lexer(split_pattern, sub_pattern, exp_type, flags))

def connect_front_end(*tuple_of_lst):
    """
    Connect front ends together
    by making use of post_proc parameter of make_front_end

    """
    lst_of_lst = scm.tuple_to_lst(tuple_of_lst)
    def extract_func(lst_of_lst): return scm.caar(lst_of_lst)
    def extract_arg_lst(lst_of_lst): return scm.cdar(lst_of_lst)
    def connect_loop(lst_of_lst, accum):
        if lst_of_lst is scm.nil:
            return accum
        else:
            return connect_loop(scm.cdr(lst_of_lst),
                                scm.apply(extract_func(lst_of_lst),
                                          scm.cons(accum,
                                                   extract_arg_lst(lst_of_lst))))
    return connect_loop(lst_of_lst, identity)

# These are patterns used to determined how to decomposite the text
# into sensible parts

TITLE_SPLIT_PATTERN = r"^(#[ \t]+[- \tA-Z]+[ \t]*)$"
TITLE_SUB_PATTERN = r"^#[ \t]+([- \tA-Z]+)[ \t]*$"

SUBTITLE_SPLIT_PATTERN = r"^(#{2,3}[ \t]+[^#\n]+#*[ \t]*)$"
SUBTITLE_SUB_PATTERN = r"^#{2,3}[ \t]+([^#\n]+)#*[ \t]*$"

HYPHEN_SPLIT_PATTERN = r"^([ \t]*-[ \t]+.+)$"
HYPHEN_SUB_PATTERN = r"^[ \t]*-[ \t]+(.+)$"

ASTERISK_SPLIT_PATTERN = r"^(\*[ \t]+[^\*\n]+)$"
ASTERISK_SUB_PATTERN = r"^\*[ \t]+([^\*\n]+)$"

NUMBER_PATTERN = r"^(\d+\.[ \t]+.+)"

VERBATIM_SPLIT_PATTERN = r"(```[^`]+```)"
VERBATIM_SUB_PATTERN = r"```([^`]+)```"

# tree representing the structure of README

AST = compose(connect_front_end(scm.list(make_front_end,
                                         VERBATIM_SPLIT_PATTERN,
                                         VERBATIM_SUB_PATTERN,
                                         scm.string_to_symbol("VERBATIM")),
                                scm.list(make_front_end,
                                         NUMBER_PATTERN,
                                         NUMBER_PATTERN,
                                         scm.string_to_symbol("NUMBER"),
                                         re.MULTILINE),
                                scm.list(make_front_end,
                                         ASTERISK_SPLIT_PATTERN,
                                         ASTERISK_SUB_PATTERN,
                                         scm.string_to_symbol("ASTERISK"),
                                         re.MULTILINE),
                                scm.list(make_front_end,
                                         HYPHEN_SPLIT_PATTERN,
                                         HYPHEN_SUB_PATTERN,
                                         scm.string_to_symbol("HYPHEN"),
                                         re.MULTILINE),
                                scm.list(make_front_end,
                                         SUBTITLE_SPLIT_PATTERN,
                                         SUBTITLE_SUB_PATTERN,
                                         scm.string_to_symbol("SUBTITLE"),
                                         re.MULTILINE),
                                scm.list(make_front_end,
                                         TITLE_SPLIT_PATTERN,
                                         TITLE_SUB_PATTERN,
                                         scm.string_to_symbol("TITLE"),
                                         re.MULTILINE)),
              remove_table_of_content) \
              (README)

def fetch_symbol(ast, exp_type_lst):
    """
    From ast, fetch symbol which is of type listed in exp_type_lst

    Note that the output is a nested lst needed to be flatten in order to be
    lst of the form (<exp_type> <exp_symbol> <exp_type> <exp_symbol> ...)

    """
    def is_not_null(s_exp): return s_exp is not scm.nil
    def is_exp(s_exp): return scm.is_list(scm.car(s_exp))
    def is_exp_type(s_exp, exp_type): return scm.caar(s_exp) is exp_type
    def extract_exp(s_exp): return scm.car(s_exp)
    def extract_rest(s_exp): return scm.cdr(s_exp)
    if not scm.is_list(ast):
        return scm.nil
    elif is_exp(ast) and \
         scm.any(lambda exp_type: is_exp_type(ast, exp_type), exp_type_lst):
        return scm.list(extract_exp(ast),
                        fetch_symbol(extract_rest(ast), exp_type_lst))
    else:
        return scm.append(scm.filter(is_not_null,
                                     scm.map(lambda sub_tree: \
                                             fetch_symbol(sub_tree,
                                                          exp_type_lst),
                                             ast)))

def group_adj_element(lst):
    """
    Take output of fetch_symbol as input

    Transform lst of the form
    (<exp_type> <exp_symbol> <exp_type> <exp_symbol> ...)
    into lst of the form
    ((<exp_type> <exp_symbol>) (<exp_type> <exp_symbol>) ...)

    """
    def index_to_element(k): return scm.list_ref(lst, k)
    lst_of_index_lst = scm.map(scm.list,
                               scm.filter(scm.is_even,
                                          scm.iota(scm.length(lst))),
                               scm.filter(scm.is_odd,
                                          scm.iota(scm.length(lst))))
    return scm.map(lambda index_lst: scm.map(index_to_element, index_lst),
                   lst_of_index_lst)

EXP_TYPE_LST = scm.list(scm.string_to_symbol("TITLE"),
                        scm.string_to_symbol("SUBTITLE"),
                        scm.string_to_symbol("HYPHEN"),
                        scm.string_to_symbol("ASTERISK"),
                        scm.string_to_symbol("NUMBER"),
                        scm.string_to_symbol("VERBATIM"))

# table recording the expression type of each expression symbol

SYMBOL_TABLE = compose(group_adj_element, flatten) \
               (fetch_symbol(AST, EXP_TYPE_LST))

def is_list_of_string(lst): return scm.every(scm.is_string, lst)

def is_contain_string_lst(s_exp):
    if not scm.is_list(s_exp):
        return False
    elif is_list_of_string(s_exp):
        return True
    else:
        return scm.any(is_contain_string_lst, s_exp)

def join_string_lst(s_exp):
    if not scm.is_list(s_exp):
        return s_exp
    elif is_list_of_string(s_exp):
        return string_join(s_exp, "")
    else:
        return scm.map(join_string_lst, s_exp)

def recursively_join_string_lst(s_exp):
    if not is_contain_string_lst(s_exp):
        return s_exp
    else:
        return recursively_join_string_lst(join_string_lst(s_exp))

def process_ast(proc, exp_type, ast):
    """recursively apply proc with exp_type, exp_symbol and rest"""
    def is_exp(s_exp): return scm.is_list(scm.car(s_exp))
    def is_exp_type(s_exp, exp_type): return scm.caar(s_exp) is exp_type
    def s_exp_first(s_exp): return scm.car(flatten(s_exp))
    def extract_exp_symbol(s_exp): return scm.cadar(s_exp)
    def extract_rest(s_exp): return s_exp_first(scm.cadr(ast))
    if not scm.is_list(ast):
        return ast
    elif is_exp(ast) and is_exp_type(ast, exp_type):
        return proc(exp_type, extract_exp_symbol(ast), extract_rest(ast))
    else:
        return scm.map(lambda sub_tree: process_ast(proc, exp_type, sub_tree),
                       ast)

def make_back_end(proc, exp_type):
    """recursively join processed tree-like structure back to string"""
    return lambda ast: recursively_join_string_lst(process_ast(proc,
                                                               exp_type,
                                                               ast))

def verbatim_processor(exp_type, exp_symbol, rest):
    """
    Create verbatim paragraph from expression with exp_type VERBATIM

    1. remove formatter name if exists
    2. indent each sentance in the paragraph by 4 spaces

    """
    def remove_formatter_name(string):
        pattern = r"^bash[ \t]*$|^python[ \t]*$"
        return re.sub(pattern, r"", string, 0, re.MULTILINE)
    def indent_by_4_spaces(string):
        pattern = r"^(.+)"
        return re.sub(pattern, r"    \1", string, 0, re.MULTILINE)
    return indent_by_4_spaces(remove_formatter_name(exp_symbol)) + rest

def group_by_exp_type(exp_type, lst):
    """group exp_type expression by removing non-exp_type expression"""
    def is_exp_type(s_exp): return scm.car(s_exp) is exp_type
    sublst = non_nil_take_while(is_exp_type, lst)
    if sublst is scm.nil:
        return scm.nil
    else:
        return scm.cons(sublst,
                        group_by_exp_type(exp_type,
                                          list_subtract(lst, sublst)))

def make_item_position_decider(func):
    """
    Return a procedure which will decide if a given string of exp_type
    is in the desired position specified by func

    func take a lst and return element of the desired position

    """
    def extract_exp_symbol(s_exp): return scm.cadr(s_exp)
    def is_item_position(string, exp_type, symbol_table):
        return scm.any(lambda exp_symbol: exp_symbol == string,
                       scm.map(compose(extract_exp_symbol, func),
                               group_by_exp_type(exp_type, symbol_table)))
    return is_item_position

def process_item(exp_type, prefix, rest, exp_symbol, symbol_table):
    """process item based on the position of exp_symbol in the symbol_table"""
    is_first_item = make_item_position_decider(scm.first)
    is_last_item = make_item_position_decider(scm.last)
    if is_first_item(exp_symbol, exp_type, symbol_table):
        return "=over 7\n\n=item Z<>" + prefix + "\n\n" + rest + "\n"
    elif is_last_item(exp_symbol, exp_type, symbol_table):
        return "=item Z<>" + prefix + "\n\n" + rest + "\n\n=back"
    else:
        return "=item Z<>" + prefix + "\n\n" + rest + "\n"

def make_item_processor(symbol_table):
    """
    Return a procedure which does a case dispatch on exp_type of expression
    and pass the extracted parts of expression to process_item

    """
    def make_number_item_lst(exp_symbol):
        split_pattern = r"^(\d+\.[ \t]+)"
        sub_pattern = r"^(\d+\.)[ \t]+"
        return scm.filter(is_not_empty_string,
                          make_lexer(split_pattern,
                                     sub_pattern,
                                     scm.string_to_symbol("NUMBER"),
                                     re.MULTILINE) \
                          (exp_symbol))
    def is_exp_type(exp_type, exp_symbol): return exp_type is exp_symbol
    def extract_prefix(number_item_lst): return scm.cadar(number_item_lst)
    def extract_rest(number_item_lst): return scm.cadr(number_item_lst)
    def process_different_items(exp_type, exp_symbol, rest):
        if is_exp_type(exp_type, scm.string_to_symbol("HYPHEN")):
            return process_item(exp_type,
                                "-",
                                exp_symbol,
                                exp_symbol,
                                symbol_table) + \
                                rest
        elif is_exp_type(exp_type, scm.string_to_symbol("ASTERISK")):
            return process_item(exp_type,
                                "*",
                                exp_symbol,
                                exp_symbol,
                                symbol_table) + \
                                rest
        elif is_exp_type(exp_type, scm.string_to_symbol("NUMBER")):
            return process_item(exp_type,
                                extract_prefix(make_number_item_lst(exp_symbol)),
                                extract_rest(make_number_item_lst(exp_symbol)),
                                exp_symbol,
                                symbol_table) + \
                                rest
        else:
            raise TypeError("unknown exp_type of expression")
    return process_different_items

def installation_section_processor(exp_type, exp_symbol, rest):
    return ""

def append_title(string):
    return "=head1 " + string + "\n\n"

def subtitle_processor(exp_type, exp_symbol, rest):
    return "=head2 " + exp_symbol + "\n\n" + rest

def name_section_processor(exp_type, exp_symbol, rest):
    """add a proper SYNOPSIS section after the NAME section"""
    synopsis = "\n\n=head1 SYNOPSIS\n\nB<<< youtube-dl >>> [I<<< OPTIONS >>>] I<<< URL >>> [I<<< URL >>>...]\n\n"
    return append_title(exp_symbol) + rest + synopsis

def description_section_processor(exp_type, exp_symbol, rest):
    """remove the improper synopsis in the DESCRIPTION section"""
    def remove_synopsis_in_description(string):
        pattern = r"^ +.+$"
        return re.sub(pattern, r"", string, 0, re.MULTILINE)
    return append_title(exp_symbol) + remove_synopsis_in_description(rest)

def sentence_per_line_to_word_per_line(string):
    def spaces_to_newline(string):
        pattern = r" +"
        return re.sub(pattern, r"\n", string, 0, re.MULTILINE)
    def remove_leading_newlines(string):
        pattern = r"^\n+"
        return re.sub(pattern, r"", string, 0, re.MULTILINE)
    def multiple_newlines_to_single_newline(string):
        pattern = r"\n+"
        return re.sub(pattern, r"\n", string, 0, re.MULTILINE)
    return compose(multiple_newlines_to_single_newline,
                   remove_leading_newlines,
                   spaces_to_newline) \
                   (string)

def process_options(string):
    """process options in the OPTIONS section"""
    def short_long_opt_with_arg_processor(string):
        pattern = r"^(-[^\s]+)[\s]*,[\s]*(--[^\s]+)[\s]+([^a-z\s]+)[\s]+([A-Z].+)$"
        return re.sub(pattern, r"\n=item\nB<<< \1 >>>\n,\nB<<< \2 >>>\nI<<< \3 >>>\n\n\4", string, 0, re.MULTILINE)
    def short_long_opt_without_arg_processor(string):
        pattern = r"^(-[^\s]+)[\s]*,[\s]*(--[^\s]+)[\s]+([A-Z].+)$"
        return re.sub(pattern, r"\n=item\nB<<< \1 >>>\n,\nB<<< \2 >>>\n\n\3", string, 0, re.MULTILINE)
    def long_opt_with_arg_processor(string):
        pattern = r"^(--[^\s]+)[\s]+([^a-z\s]+)[\s]+([A-Z].+)$"
        return re.sub(pattern, r"\n=item\nB<<< \1 >>>\nI<<< \2 >>>\n\n\3", string, 0, re.MULTILINE)
    def long_opt_without_arg_processor(string):
        pattern = r"^(--[^\s]+)[\s]+([A-Z].+)$"
        return re.sub(pattern, r"\n=item\nB<<< \1 >>>\n\n\2", string, 0, re.MULTILINE)
    return compose(long_opt_without_arg_processor,
                   long_opt_with_arg_processor,
                   short_long_opt_without_arg_processor,
                   short_long_opt_with_arg_processor,
                   sentence_per_line_to_word_per_line) \
                   (string)

def options_section_processor(exp_type, exp_symbol, rest):
    """
    Process the OPTIONS section by creating a sub_tree using front_end and
    use process_options to process scm.cdr(sub_tree)

    Finally, convert the sub_tree back into string using back_end

    """
    def options_subsections_processor(exp_type, exp_symbol, rest):
        return "\n=back\n\n=head2 " + \
            exp_symbol + \
            "\n\n=over 7\n\n" + \
            process_options(rest)
    subtitle_split_pattern = r"^(=head2 .+)$"
    subtitle_sub_pattern = r"^=head2 (.+)$"
    sub_tree = connect_front_end(scm.list(make_front_end,
                                          subtitle_split_pattern,
                                          subtitle_sub_pattern,
                                          scm.string_to_symbol("SUBTITLE"),
                                          re.MULTILINE)) \
                                          (rest)
    return append_title(exp_symbol) + \
        "=over 7\n\n" + \
        make_back_end(options_subsections_processor,
                      scm.string_to_symbol("SUBTITLE")) \
                      (scm.cons(process_options(scm.car(sub_tree)),
                                scm.cdr(sub_tree))) + \
                                "\n=back\n\n"

def title_processor(exp_type, exp_symbol, rest):
    """do a case dispatch on exp_type and invoke the appropriate processor"""
    if exp_symbol == "INSTALLATION":
        return installation_section_processor(exp_type, exp_symbol, rest)
    elif exp_symbol == "NAME":
        return name_section_processor(exp_type, exp_symbol, rest)
    elif exp_symbol == "DESCRIPTION":
        return description_section_processor(exp_type, exp_symbol, rest)
    elif exp_symbol == "OPTIONS":
        return options_section_processor(exp_type, exp_symbol, rest)
    else:
        return append_title(exp_symbol) + rest

def bold(string):
    """enclose string marked as bold by B<<< >>>"""
    pattern = r"\*\*([^\*\n]+)\*\*"
    return re.sub(pattern, r"B<<< \1 >>>", string, 0, re.MULTILINE)

def italic(string):
    """enclose string marked as italic by I<<< >>>"""
    def asterisk_to_italic(string):
        pattern = r"\*([^\*\n]+)\*"
        return re.sub(pattern, r"I<<< \1 >>>", string, 0, re.MULTILINE)
    def back_quote_to_italic(string):
        pattern = r"`{1,2}([^`\n]+)`{1,2}"
        return re.sub(pattern, r"I<<< \1 >>>", string, 0, re.MULTILINE)
    return compose(back_quote_to_italic, asterisk_to_italic) \
        (string)

def remove_internal_links(string):
    pattern = r"\[([^]|\n]+)\]\(#[^\)|\n]+\)"
    return re.sub(pattern, r"\1", string, 0, re.MULTILINE)

def external_links(string):
    """convert external links of the form [foo](bar) into L<<< foo|bar >>>"""
    pattern = r"\[([^]|\n]+)\]\(([^\)|\n]+)\)"
    return re.sub(pattern, r"L<<< \1|\2 >>>", string, 0, re.MULTILINE)

# First, convert AST back to string using various back_ends
# Finally, postprocess the string and display it
scm.display(compose(external_links,
                    remove_internal_links,
                    italic,
                    bold,
                    make_back_end(title_processor,
                                  scm.string_to_symbol("TITLE")),
                    make_back_end(subtitle_processor,
                                  scm.string_to_symbol("SUBTITLE")),
                    make_back_end(make_item_processor(SYMBOL_TABLE),
                                  scm.string_to_symbol("HYPHEN")),
                    make_back_end(make_item_processor(SYMBOL_TABLE),
                                  scm.string_to_symbol("ASTERISK")),
                    make_back_end(make_item_processor(SYMBOL_TABLE),
                                  scm.string_to_symbol("NUMBER")),
                    make_back_end(verbatim_processor,
                                  scm.string_to_symbol("VERBATIM"))) \
            (AST))
