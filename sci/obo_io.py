#!/usr/bin/env python3

"""
    obo_io.py

    python .obo file parser and writer for the obo 1.2 spec defined at
    https://oboformat.googlecode.com/svn/trunk/doc/GO.format.obo-1_2.html
"""
import os
from collections import OrderedDict as od
from IPython import embed

N = -1  # use to define 'many ' for tag counts

od.__repr__ = dict.__repr__

class OboFile:
    type_def = ('<header>','<stanza>')
    def __init__(self, filename=None, header=None, terms=None, typedefs=None, instances=None):
        self.filename = filename
        if filename is not None or header is None:  # FIXME could spec filename here?
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
                block_type, block = block.split(']\n',1)
                type_ = stanza_types[block_type]
                type_(block, self)
        else:
            self.header = header
            self.Terms = terms
            self.Typedefs = typedefs
            self.Instances = instances

    def write(self, filename):
        if os.path.exists(filename):
            name, ext = filename.rsplit('.',1)
            try:
                prefix, num = name.rsplit('_',1)
                n = int(num)
                n += 1
                filename = prefix + '_' + str(n) + '.' + ext
            except:
                filename = name + '_1.' + ext
                raise
            print('file exists, renaming to %s' % filename)
            self.write(filename)


        with open(filename, 'wt') as f:
            f.write(str(self))

    def __str__(self):
        stores = [str(self.header)]
        stores += [str(s) for s in self.Terms.values()]
        stores += [str(s) for s in self.Typedefs.values()] 
        stores += [str(s) for s in self.Instances.values()]
        return '\n'.join(stores) + '\n'

    def __repr__(self):
        s = 'OboFile instance with %s Terms, %s Typedefs, and %s Instances' % (
            len(self.Terms), len(self.Typedefs), len(self.Instances))

        return s

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
    def __init__(self, line=None, tag=None, value=None, modifiers=None, comment=None):
        if line is not None:
            tag, value, trailing_modifiers, comment = self.parse(line)
            self.tag = tag
            self.value = value
            self.trailing_modifiers = trailing_modifiers
            self.comment = comment
            self.validate(warn=True)
        else:
            self.tag = tag
            self.value = value
            self.trailing_modifiers = modifiers
            self.comment = comment
            self.validate()

    def validate(self, warn=False):  # TODO
        # 
        #warn if we are loading an ontology and there is an error but don't fail
        #id
        #name
        #def
        #synonym
        if not warn:
            print('PLS IMPLMENT ME! ;_;')

    def __str__(self):
        string = "{}: {}".format(self.tag, self.value)
        if self.trailing_modifiers:
            string += " " + str(self.trailing_modifiers)
        if self.comment:
            # TODO: autofill is_a comments
            string += " ! " + self.comment
        return string

    def __repr__(self):
        return str(self)

    @staticmethod
    def esc(string):
        for f, r in TVPair._escapes:
            string = string.replace(f, r)
        return string

    @staticmethod
    def esc_(string):
        """ fix strings for use as names in classes """
        if string == 'id':  # dont clobber id
            return 'id_'
        return string.replace('-','_').replace(':','')

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
    _runonce = True
    def __new__(cls, *args, **kwargs):
        if cls._runonce:
            cls._tags = od()
            for tag, limit in cls._all_tags:
                cls._tags[tag] = limit
            cls._runonce = False
        return super().__new__(cls)  # FIXME somehow this is overwriting updated _tags?

    def __init__(self, block=None, tvpairs=None):
        # keep _tags out of self.__dict__ and add new tags for all instances
        for tag, limit in self._tags.items():
            if limit == N:
                self.__dict__[TVPair.esc_(tag)] = []  # may need a list

        if block is not None:
            lines = block.split('\n')
            for line in lines:
                if line:
                    tvpair = TVPair(line)
                    self.add_tvpair(tvpair)
            warn = True
        else:
            for tvpair in tvpairs:
                self.add_tvpair(tvpair)
            warn = False

        #clean up empty tags
        to_pop = []
        for tag, value in self.__dict__.items():
            if not value:
                to_pop.append(tag)

        for tag in to_pop:
            self.__dict__.pop(tag)

        self.validate(warn)
            
    def add_tvpair(self, tvpair):
        tag = tvpair.tag
        dict_tag = TVPair.esc_(tag)

        if tag not in self._tags:
            print('TAG NOT IN', tag)
            self._tags[tag] = N  # FIXME why does this not set the value?!
            print(self._tags[tag])
            self.__dict__[dict_tag] = []

        if self._tags[tag] == N:
            self.__dict__[dict_tag].append(tvpair)
        else:
            self.__dict__[dict_tag] = tvpair

    @property
    def tvpairs(self):
        index = tuple(self._tags)
        print(index)

        def key_(tvpair):
            #print(index)
            #print(tvpair.tag)
            out = index.index(tvpair.tag)
            if self._tags[tvpair.tag] == N:
                sord = sorted([tvp.value for tvp in self.__dict__[tvpair.tag]])
                #subsort multi tags by their value, +1 to ensure < next int tag
                out += sord.index(tvpair.value) / (len(sord) + 1)
            return out
            
            #try:
            #except ValueError:
                #print('TAG FAIL',tvpair)
                # if we fail put the unknowns at the end in original order
                #sort = len(index) + tuple(self.__dict__.keys()).index(tvpair.tag)
                #return sort
        tosort = []
        for tvp in self.__dict__.values():
            if type(tvp) == list:
                tosort.extend(tvp)
            else:
                tosort.append(tvp)
        return sorted(tosort, key=key_)

    def __str__(self):
        return '\n'.join(str(tvpair) for tvpair in self.tvpairs) + '\n'

    def __repr__(self):
        return ' '.join(str(tvpair) for tvpair in self.tvpairs) + ' '

    def validate(self, warn=False):
        tags = []
        for tag, tvp in self.__dict__.items():
            #print(tvp)
            if tvp:
                if type(tvp) == list:
                    tags.append(tvp[0].tag)
                else:
                    try:
                        tags.append(tvp.tag)
                    except AttributeError:
                        embed()
                        raise
            else:
                raise AttributeError('Tag %s has no values!' % tag)

        for tag in self._r_tags:
            if tag not in tags:
                if warn:
                    raise ImportWarning('%s %s is missing a required tag %s' %
                                        (self.__class__.__name__, str(self), tag))
                else:
                    raise AttributeError('%s must have a tag of type %s' %
                                         (self.__class__.__name__, tag))

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
        ('import', N),
        ('subsetdef', N),
        ('synonymtypedef', N),
        ('default-namespace', 1),
        ('remark', N),
        ('ontology', 1),
        #'idspace',
        #'default-relationship-id-previx',
        #'id-mapping',
    )
    #def __new__(cls, *args, **kwargs):
        ##cls._tags = cls._all_tags
        #return super().__new__(cls, *args, **kwargs)

class Stanza(TVPairStore):
    _type_ = '<stanza>'
    _type_def = ('[<Stanza name>]','<tag-value pair>')
    _r_tags = ['id', 'name',]
    _all_tags = (
        ('id', 1),
        ('is_anonymous', 1),
        ('name',1),
        ('namespace', 1),
        ('alt_id', N), 
        ('def', 1),
        ('comment', 1),
        ('subset', N),
        ('synonym', N),
        ('acronym', N),  # i think it is just better to add this
        ('xref', N),
        ('instance_of', 1), ##
        ('property_value', N), ##
        ('domain', 1), #
        ('range', 1), #
        ('is_anti_symmetric', 1), #
        ('is_cyclic', 1), #
        ('is_reflexive', 1), #
        ('is_symmetric', 1), #
        ('is_transitive', 1), #
        ('is_a', 1),
        ('inverse_of', 1), #
        ('transitive_over', N), #
        ('intersection_of', N),  # no relationships, typedefs
        ('union_of', N),  # min 2, no relationships, typedefs
        ('disjoint_from', N),  # no relationships, typedefs
        ('relationship', N),
        ('is_obsolete', 1),
        ('replaced_by', N),
        ('consider', N),
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
    def __new__(cls, *args, **kwargs):
        if cls._runonce:
            # if we don't wrap this it will overwrite _all_tags and ultimately update _tags
            cls._all_tags = [tag for tag in cls._all_tags if tag[0] not in cls._bad_tags]
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, block=None, obofile=None, tvpairs=None):
        if block is not None and obofile is not None:
            super().__init__(block)
            type_od = getattr(obofile, self.__class__.__name__+'s')
            type_od[self.id_.value] = self  # atm we need names
            type_od.__dict__[TVPair.esc_(self.id_.value)] = self  # FIXME
        else:
            super().__init__(tvpairs)

    def __str__(self):
        return '['+ self.__class__.__name__ +']\n' + super().__str__()

class Term(Stanza):
    #type_ = 'Term'
    _bad_tags = ['instance_of', 'property_value']
    def __new__(cls, *args, **kwargs):
        cls._bad_tags = cls._typedef_only_tags + cls._typedef_only_tags
        return super().__new__(cls, *args, **kwargs)

class Typedef(Stanza):
    #type_ = 'Typedef'
    _bad_tags = ('union_of', 'intersection_of', 'disjoint_from', 'instance_of', 'property_value')
    #def __new__(cls, *args, **kwargs):
        #super().__new__(cls, *args, **kwargs)


class Instance(Stanza):
    #type_ = 'Instance'
    _r_tags = ['instance_of',]
    def __new__(cls, *args, **kwargs):
        cls._bad_tags = cls._typedef_only_tags + cls._typedef_only_tags
        cls._r_tags = super()._r_tags + cls._r_tags
        return super().__new__(cls, *args, **kwargs)


stanza_types = {type_.__name__:type_ for type_ in (Term, Typedef, Instance)}

def deNone(*args):
    for arg in args:
        if arg == None:
            yield ''
        else:
            yield arg

def main():
    #folder = '/home/tom/ni/protocols/'
    folder = 'C:/Users/root/Dropbox/neuroinformatics/protocols/'
    #filename = folder + 'go.obo'
    filename = folder + 'ksm_utf8_2.obo'
    of = OboFile(filename=filename)
    embed()

if __name__ == '__main__':
    main()
