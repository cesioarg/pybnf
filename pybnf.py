import regex as re
from regex import compile as Regex, sub as regex_replace

convert_whitespace = lambda src:regex_replace("\s\s+"," ", src)


def in_range(range1, range2):
    if range1[0] >= range2[0] and range1[0] <= range2[1]:
        if range1[1] >= range2[0] and range1[1] <= range2[1]:
            return True
    return False


def range(match, field):
    return zip(match.starts(field), match.ends(field))


class Matches(object):
    def __init__(self, match):
        self.match = match


class GrammarParser(object):
    rule_searcher = Regex('([^\s]+)\s*=(.*)', re.MULTILINE)

    def __init__(self, grammar_text, text):
        self.grammar_text = grammar_text.strip()
        self._rules = {}
        self._rules = list(iter(self))
        self.text = text
        self.data = {}

    def get_data(self, main):
        nested_match = {}

        match = re.match(getattr(self, main), self.text)
        match_dict = match.capturesdict()

        for name, rule in self:
            if name == main:
                for field in rule.fields:
                    if field in match_dict:
                        print name, field

        for label in match_dict:
            print label
            for item in zip(match.starts(label), match.ends(label)):
                print item

    @property
    def match(self):
        if not '_match' in dir(self):
            self._match = re.match(getattr(self, 'file'), self.text)

        return self._match

    @property
    def match_dict(self):
        return self.match.capturesdict()

    def print_tree(self, main, data={}):
        data[main.name] = {}

        for field in main.fields:
            if field in self.match_dict:
                data[main.name][field] = []

                for par_idx, parent_range in enumerate(range(self.match, main.name)):
                    capt = self.match.captures(field)
                    for fld_idx, field_range in enumerate(range(self.match, field)):
                        if in_range(field_range, parent_range):
                            data[main.name][field].append(field_range)

                    yield data
                    #print main.name, parent_range, field, field_range

                for item in self.print_tree(self[field]):
                    yield item

    def __getattribute__(self, attr):
        for rule in object.__getattribute__(self, '_rules'):
            if rule.name == attr:
                try:
                    name = str(rule)
                    for field in rule.fields:
                        name = name.replace('{%s}' % field, self.__getattribute__(field))
                    raise AttributeError
                    
                except AttributeError:
                    raise Exception("Can't find '" + field + "' attribute.")
                finally:
                    return name         #.replace('(', '(?P<%s>' % attr)
        else:
            return object.__getattribute__(self, attr)

    def __contains__(self, item):
        for rule in self._rules:
            if rule.name == item:
                return True
        return False

    def __getitem__(self, item):
        for rule in self._rules:
            if rule.name == item:
                return rule

    def __iter__(self):
        for match in self.rule_searcher.finditer(self.grammar_text):
            rule_name = convert_whitespace(match.group(1)).strip()
            rule_definition = convert_whitespace(match.group(2)).strip().replace('(', '(?P<%s>' % rule_name)
            yield RuleParser(rule_name, rule_definition)


class RuleParser(object):
    def __init__(self, name, rule):
        self.name = name
        self.rule = rule

    def __getitem__(self, item):
        index = 0
        if isinstance(item, int):
            for field in self.fields:
                if index == item:
                    return field
                index += 1

        elif isinstance(item, basestring):
            for field in self.fields:
                if field == item:
                    return index
                index += 1

    def __str__(self):
        return self.rule 

    def __repr__(self):
        return str(self)

    def __iter__(self):
        for part in self.rule[1:].split('{'):
            yield part[:part.find('}')]
            yield part[part.find('}') + 1:]

    def __contains__(self, item):
        if isinstance(item, basestring):
            for field in self.fields:
                if field == item:
                    return True

    @property
    def lenFields(self):
        index = 0
        for field in self.fields:
            index +=1
        return index

    @property
    def lenSeparators(self):
        index = 0
        for field in self.separators:
            index +=1
        return index

    @property
    def fields(self):
        index = 0
        for part in self.rule.split('{'):
            if '}' in part:
                yield part[:part.find('}')]
            index += 1

    @property
    def separators(self):
        index = 0
        for part in self.rule.split('{'):
            yield part[part.find('}') + 1:]
            index += 1


if __name__ == '__main__':
    sample_ebnf = r"""
        file                    = ({header}{content})
        header               = {shebang}{version}
        shebang             = (#!\s*{word}\s*-[a-zA-Z0-9]+\n)
        version               = (version\s*[0-9].[0-9]\s*v[0-9]\n)
        content              = ({node})*
        node                  = ({nodename}\s*{\n{nodecontent}\n})\n
        nodecontent       = (\s*{knobname}\s*{knobvalue}\s*\n*)*
        knobname          = ({word})
        knobvalue          = ({word}|{string}|{knobgroup}|{multiknobgroup})
        knobgroup         = ({({word}\s*|{string}\s*)*\s*})
        multiknobgroup  = ({\n*(\s*{knobgroup}\s*\n*)*})
        string                = "([a-zA-Z0-9-_()/\~.<>?;: ]*)"
        nodename         = ({word})
        word                 = ([a-zA-Z0-9-_()/\~.<>?;:]*)
    """

    script = """#! /opt/foundry/Nuke/6.3v7-x64/Nuke6.3 -nx
version 6.3 v7
Root {
    inputs 0
    name /path/to/file_name.nk
    first_frame 0
    last_frame 100
    lock_range true
    format "2048 1556 0 0 2048 1556 1 2K_Super_35(full-ap)"
    proxy_type scale
    proxy_format "1024 778 0 0 1024 778 1 1K_Super_35(full-ap)"
    addUserKnob {20 custom l Custom}
    addUserKnob {1 scene l Scene}
    views {
        {left ""}
        {right ""}
    }
}
"""
    rp = GrammarParser(sample_ebnf, script)
    for item in rp.print_tree(rp._rules[0]):
        print item
        #print script[item[2][0]:item[2][1]]
    
    #rp.get_data('file')
