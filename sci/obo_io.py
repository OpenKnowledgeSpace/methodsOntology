#!/usr/bin/env python3

from collections import OrderedDict as od
from IPython import embed

n = -1  # use to define 'many ' for tag counts

od.__repr__ = dict.__repr__

class OboFile:
    type_def = ('<header>','<stanza>')
    def __init__(self, filename):
        with open(filename, 'rt') as f:
            data = f.read()
        #deal with \<newline> escape
        data = data.replace(' \n','\n')  # FXIME need for arbitrary whitespace
        data = data.replace('\<newline>\n',' ')
        sections = data.split('\n[')
        header_block = sections[0]
        self.header = Header(header_block)
        stanzas = sections[1:]
        self.Terms = od()
        self.Typedefs = od()
        self.Instances = od()
        for block in stanzas:
            name, block = block.split(']\n',1)
            type_ = stanza_types[name]
            type_(block, self)

    def __str__(self):
        stores = [str(self.header)]
        stores += [str(s) for s in self.Terms.values()]
        stores += [str(s) for s in self.Typedefs.values()] 
        stores += [str(s) for s in self.Instances.values()]
        return '\n'.join(stores)

    def __repr__(self):
        stores = [repr(self.header)]
        stores += [repr(s) for s in self.Terms.values()]
        stores += [repr(s) for s in self.Typedefs.values()] 
        stores += [repr(s) for s in self.Instances.values()]
        return '\n'.join(stores)

class TVPair:
    _type_ = '<tag-value pair>'
    _type_def = ('<tag>', '<value>', '{<trailing modifiers>}', '<comment>')
    _escapes = {
        '\\n':'\n',
        '\W':' ',
        '\\t':'\t',
        '\:':':',
        '\,':',',
        '\\"':'"',
        '\\\\':'\\',
        '\(':'(',
        '\)':')',
        '\[':'[',
        '\]':']',
        '\{':'{',
        '\}':'}',
              }
    def __init__(self, line):
        tag, value, trailing_modifiers, comment = self.parse(line)
        self.tag = tag
        self.value = value
        self.trailing_modifiers = trailing_modifiers
        self.comment = comment

    def __str__(self):
        string = "{}: {}".format(self.tag, self.value)
        if self.trailing_modifiers:
            string += " " + str(self.trailing_modifiers)
        if self.comment:
            string += " ! " + self.comment
        return string

    def __repr__(self):
        return str(self)

    @staticmethod
    def parse(line):
        try:
            tag, value = line.split(':',1)
        except ValueError:
            embed()
            raise
        value, trailing_modifiers, comment = TVPair.parse_value(value)
        return tag, value, trailing_modifiers, comment

    @staticmethod
    def parse_value(value):  # TODO
        return value.strip().rstrip(), None, None

class TVPairStore:
    def __init__(self, block):
        lines = block.split('\n')
        for line in lines:
            if line:
                tvpair = TVPair(line)
                if tvpair.tag == 'id':
                    self.__dict__['id_'] = tvpair  # don't clobber id
                else:
                    self.__dict__[tvpair.tag.replace('-','_')] = tvpair

    @property
    def tvpairs(self):
        index = [c for c in zip(*self._tags)][0]  # TODO terms not in order at end?

        def key_(tvpair):
            try:
                return index.index(tvpair.tag)
            except ValueError:
                print('TAG FAIL',tvpair)
                # if we fail put the unknowns at the end in original order
                sort = len(index) + tuple(self.__dict__.keys()).index(tvpair.tag)
                return sort

        return sorted([tvp for tvp in self.__dict__.values()], key=key_)

    def __str__(self):
        return '\n'.join(str(tvpair) for tvpair in self.tvpairs) + '\n'

    def __repr__(self):
        return ' '.join(str(tvpair) for tvpair in self.tvpairs) + ' '

class Header(TVPairStore):
    _type_ = '<header>'
    _type_def = ('<tag-value pair>',)
    _r_tags = ('format-version', )
    _all_tags = (
        ('format-version', 1),
        ('data-version', 1),
        ('date', 1),
        ('saved-by', 1),
        ('auto-generated-by', 1),
        ('import', n),
        ('subsetdef', n),
        ('synonymtypedef', n),
        ('default-namespace', 1),
        ('remark', n),
        ('ontology', 1),
        #'idspace',
        #'default-relationship-id-previx',
        #'id-mapping',
    )

    def __new__(cls, *args, **kwargs):
        cls._tags = cls._all_tags
        return super().__new__(cls)



class Stanza(TVPairStore):
    _type_ = '<stanza>'
    _type_def = ('[<Stanza name>]','<tag-value pair>')
    _r_tags = ['id', 'name',]
    _all_tags = (
        ('id', 1),
        ('is_anonymous', 1),
        ('name',1),
        ('namespace', 1),
        ('alt_id', n), 
        ('def', 1),
        ('comment', 1),
        ('subset', n),
        ('synonym', n),
        ('xref', n),
        ('instance_of', 1), ##
        ('property_value', n), ##
        ('domain', 1), #
        ('range', 1), #
        ('is_anti_symmetric', 1), #
        ('is_cyclic', 1), #
        ('is_reflexive', 1), #
        ('is_symmetric', 1), #
        ('is_transitive', 1), #
        ('is_a', 1),
        ('inverse_of', 1), #
        ('transitive_over', n), #
        ('intersection_of', n),  # no relationships, typedefs
        ('union_of', n),  # min 2, no relationships, typedefs
        ('disjoint_from', n),  # no relationships, typedefs
        ('relationship', n),
        ('is_obsolete', 1),
        ('replaced_by', n),
        ('consider', n),
        ('created_by', 1),
        ('creation_date', 1),
    )
    _typedef_only_tags = [
        'domian',
        'range',
        'inverse_of',
        'transitive_over',
        'is_cyclic',
        'is_reflexive',
        'is_symmetric',
        'is_anti_symmetric',
        'is_transitive',
        'is_metadata_tag',
    ]
    _types = ('Term', 'Typedef', 'Instance')

    def __init__(self, block, obofile):
        super().__init__(block)
        type_od = getattr(obofile, self.__class__.__name__+'s')
        type_od[self.name.value] = self  # atm we need names
        type_od.__dict__[self.name.value] = self

    def __str__(self):
        return '['+ self.__class__.__name__ +']\n' + super().__str__()

class Term(Stanza):
    #type_ = 'Term'
    _bad_tags = ['instance_of', 'property_value']
    def __new__(cls, *args, **kwargs):
        cls._bad_tags = cls._typedef_only_tags + cls._typedef_only_tags
        cls._tags = [tag for tag in cls._all_tags if tag[0] not in cls._bad_tags]
        return super().__new__(cls)

class Typedef(Stanza):
    #type_ = 'Typedef'
    _bad_tags = ('union_of', 'intersection_of', 'disjoint_from', 'instance_of', 'property_value')
    def __new__(cls, *args, **kwargs):
        cls._tags = [tag for tag in cls._all_tags if tag[0] not in cls._bad_tags]
        return super().__new__(cls)

class Instance(Stanza):
    #type_ = 'Instance'
    _r_tags = ['instance_of',]
    def __new__(cls, *args, **kwargs):
        cls._bad_tags = cls._typedef_only_tags + cls._typedef_only_tags
        cls._r_tags = super()._r_tags + cls._r_tags
        cls._tags = [tag for tag in cls._all_tags if tag[0] not in cls._bad_tags]
        return super().__new__(cls)

stanza_types = {type_.__name__:type_ for type_ in (Term, Typedef, Instance)}

def deNone(*args):
    for arg in args:
        if arg == None:
            yield ''
        else:
            yield arg

def main():
    folder = '/home/tom/ni/protocols/'
    #filename = folder + 'go.obo'
    filename = folder + 'ksm_utf8_1.obo'
    of = OboFile(filename)
    embed()

if __name__ == '__main__':
    main()
