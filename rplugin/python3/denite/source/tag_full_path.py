# ============================================================================
# FILE: tag_full_path.py
# AUTHOR: Dilberry
# License: MIT license
# ============================================================================

from .base import Base
from os.path import exists
import re

class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.vim = vim
        self.name = 'tag_full_path'
        self.kind = 'file'

    def on_init(self, context):
        self._tags = self._get_tagfiles(context)

    def gather_candidates(self, context):
        candidates = []
        for f in self._tags:
            with open(f, 'r', encoding=context['encoding'],
                      errors='replace') as ins:
                for line in ins:
                    if re.match('!', line) or not line:
                        continue
                    info = self.parse_tagline(line.rstrip(), f)
                    candidate = {
                        'word': info['name'],
                        'action__path': info['file'],
                    }
                    if info['type']:
                        fmt = '{name} [{type}] {file} {ref}'
                    else:
                        fmt = '{name} {file} {ref}'
                    candidate['abbr'] = fmt.format(**info)
                    if info['line']:
                        candidate['action__line'] = info['line']
                    else:
                        candidate['action__pattern'] = info['pattern']
                    candidates.append(candidate)

        return sorted(candidates, key=lambda value: value['word'])

    def _get_tagfiles(self, context):
        if (context['args'] and context['args'][0] == 'include' and
                self.vim.call('exists', '*neoinclude#include#get_tag_files')):
            tagfiles = self.vim.call('neoinclude#include#get_tag_files')
        else:
            tagfiles = self.vim.call('tagfiles')
        return [x for x in self.vim.call(
            'map', tagfiles, 'fnamemodify(v:val, ":p")') if exists(x)]

    def parse_tagline(self, line, tagpath):
        elem = line.split("\t")
        file_path = elem[1] if exists(elem[1]) else normpath(join(dirname(tagpath), elem[1]))
        info = {
            'name': elem[0],
            'file': file_path,
            'pattern': '',
            'line': '',
            'type': '',
            'ref': '',
        }

        rest = '\t'.join(elem[2:])
        m = re.search(r'.*;"', rest)
        if not m:
            if len(elem) >= 3:
                info['line'] = elem[2]
            return info

        pattern = m.group(0)
        if re.match('\d+;"$', pattern):
            info['line'] = re.sub(r';"$', '', pattern)
        else:
            info['pattern'] = re.sub(r'([~.*\[\]\\])', r'\\\1',
                                     re.sub(r'^/|/;"$', '', pattern))

        elem = rest[len(pattern)+1:].split("\t")
        if len(elem) >= 1:
            info['type'] = elem[0]
        info['ref'] = ' '.join(elem[1:])

        return info

