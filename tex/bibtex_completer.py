#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import shlex
import logging
import json
import glob
import fnmatch
import os

from ycmd.completers.completer import Completer
from ycmd import responses
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import author


LOG = logging.getLogger(__name__)

# list of commands for cite
CITE = [
    "cite",
    "citeauthor",
    "citen",
    "citep",
    "citet",
    "citeyear",
    "footcite"
]

REF = [
    "ref",
    "vref",
]


def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results


def customization(record):
    """
    A customization for the output of bibtexparser.
    """
    return author(record)


def removeNonAscii(s):
    return "".join(i for i in s if ord(i) < 128)


def _search_config_file():

    # init the current directory
    cwd = os.getcwd()
    count = 0

    # while the configuration file isn't found, up in the tree
    while ".bibtex_completer.json" not in os.listdir(cwd) and count < 100:

        # up in the tree
        os.chdir(os.path.join(cwd, ".."))

        # set current directory to up
        cwd = os.getcwd()

        # increment i case file not found
        count += 1

    # case file not found
    if count >= 100:

        # default to files in the current dir
        return {"data": glob.glob("*.bib"), "root": "."}

    # open the config for getting the list of bib files to search
    data = dict()
    data["root"] = cwd
    with open(os.path.join(cwd, ".bibtex_completer.json"), "r") as f:
        tmp = json.loads(f.read())
    data.update(tmp)

    return data


class BibTexCompleter(Completer):
    """
    Completer for LaTeX that takes into account BibTex entries
    for completion.
    """

    # LaTeX query types we are going to see
    # TODO: make this an enum
    NONE = 0
    CITATIONS = 1
    LABELS = 2

    def __init__(self, user_options):
        super(BibTexCompleter, self).__init__(user_options)
        self.complete_target = self.NONE
        LOG.info("I'm here")
        self._data = _search_config_file()
        self._CITE = CITE
        self._REF = REF
        if "cites" in self._data:
            self._CITE += self._data["cites"]
        if "references" in self._data:
            self._REF += self._data["references"]

    def DebugInfo(self, request_data):
        return "TeX completer %d" % self.complete_target

    def _search_command(self, request):

        # get some properties of the line
        line = request["line_value"]
        col = request["start_column"] - 1

        # search the regular expression
        m = re.match(r"\\(\w+)\{", line[:col])

        # get the command
        try:
            self._command = m.groups()[0]
        except AttributeError:
            self._command = "@@NULL"

    def _search_cite_list(self):

        return self._command in self._CITE

    def _search_ref_list(self):

        # check is in cites
        # check is in cites
        LOG.info("command: %s" % self._command)
        LOG.info(REF)
        return self._command in self._REF

    def ShouldUseNowInner(self, request_data):
        """
        Used by YCM to determine if we want to be called for the
        current buffer state.
        """

        # get the latex command launched
        self._search_command(request_data)

        if self._search_cite_list():
            self.complete_target = self.CITATIONS
            LOG.debug("complete target %d" % self.complete_target)
            return True

        if self._search_ref_list():
            self.complete_target = self.LABELS
            LOG.debug("complete target %d" % self.complete_target)
            return True

        return super(BibTexCompleter, self).ShouldUseNowInner(request_data)

    def SupportedFiletypes(self):
        """
        Determines which vim filetypes we support
        """
        return ['plaintex', 'tex']

    def _FindBibEntries(self):
        """
        Find BIBtex entries.

        I'm currently assuming, that Bib entries have the format
        ^@<articletype> {<ID>,
        <bibtex properties>
        [..]
        }

        Hence, to find IDs for completion, I scan for lines starting
        with an @ character and extract the ID from there.

        The search is done by a shell pipe:
        cat *.bib | grep ^@ | grep -v @string
        """
        bibs = self._data["bibtex"]
        ret = []
        if len(bibs) != 0:
            for bib in bibs:

                # open the bibtex file
                with open(os.path.expanduser(bib), "r") as f:
                    text = removeNonAscii(f.read())
                    fields = BibTexParser(
                        text,
                        customization=customization
                    ).get_entry_list()

                # get fields in each bibtex
                for article in fields:
                    info = list()
                    if "author" in article:
                        info.append("{0}".format(
                            self._remove_characters(
                                article["author"][0]
                            )
                        ))
                    if "title" in article:
                        info.append("{0}".format(
                            article["title"][:40]
                        ))
                    if "year" in article:
                        info.append("{0}".format(
                            article["year"]
                        ))
                    ret.append(responses.BuildCompletionData(
                        article["id"],
                        extra_menu_info="\t".join(info)
                        )
                    )
                    LOG.info(ret)
        return ret

    @staticmethod
    def _remove_characters(text):
        tmp = text.replace("{", "")
        tmp = tmp.replace("}", "")
        tmp = tmp.replace("~", " ")
        tmp = tmp.replace("\\", "")
        tmp = tmp.replace("\n", " ")
        return tmp

    @staticmethod
    def _to_lower(bib):
        for x in bib:
            x = {key.lower(): value for key, value in x.items()}

    def _FindLabels(self):
        """
        Find LaTeX labels for \\ref{} completion.

        This time we scan through all .tex files in the current
        directory and extract the content of all \label{} commands
        as sources for completion.
        """
        # recursively search in the root directory
        texs = " ".join(recursive_glob(self._data["root"], "*.tex"))
        cat_process = subprocess.Popen(shlex.split("cat %s" % texs),
                                       stdout=subprocess.PIPE)
        grep_process = subprocess.Popen(shlex.split(r"grep \\\\label"),
                                        stdin=cat_process.stdout,
                                        stdout=subprocess.PIPE)
        cat_process.stdout.close()

        lines = grep_process.communicate()[0]

        ret = []
        for label in lines.split("\n"):
            ret.append(responses.BuildCompletionData(
                re.sub(r".*\label{(.*)}.*", r"\1", label)
                )
            )

        return ret

    def ComputeCandidatesInner(self, request_data):
        """
        Worker function executed by the asynchronous
        completion thread.
        """
        LOG.debug("compute candidates %d" % self.complete_target)
        if self.complete_target == self.LABELS:
            return self._FindLabels()
        if self.complete_target == self.CITATIONS:
            return self._FindBibEntries()

        self.complete_target = self.NONE
        return self._FindLabels() + self._FindBibEntries()

# vim: set tw=79 :
