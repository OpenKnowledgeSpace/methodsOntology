#!/usr/bin/env python3

"""
    obo_io.py

    python .obo file parser and writer for the obo 1.2 spec defined at
    https://oboformat.googlecode.com/svn/trunk/doc/GO.format.obo-1_2.html
"""
__title__ = 'obo_io'
__author__ = 'Tom Gillespie'
import os
from getpass import getuser
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
    _reserved_ids = ('OBO:TYPE','OBO:TERM','OBO:TERM_OR_TYPE','OBO:INSTANCE')
    _datetime_fmt = '%d:%m:%Y %H:%M'  # WE USE ZULU
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

        # tag specific parsing name, encloser pairs, use for reconstruction too
        special_children = (
            ('subsetdef', ('name', ' ', 'desc', '"')),
            ('synonymtypedef', ('name', ' ', 'desc', '"',  '*scope', ' ')),
            ('idspace', ('name', ' ', 'uri', ' ', '*desc', '"')),
            ('id-mapping', ('id', ' ', 'target', ' ')),

            ('def', ('text', '"', 'xrefs', '[')),
            ('synonym', ('text', '"', '*scope', ' ', '*synonymtypedef', ' ', 'xrefs', '[')),
            ('xref', ('name', ' ', '*desc', '"')),
            ('relationship', ('typedef', ' ', 'term', ' ')),
        )
        special_children = {k:v for k, v in special_children}

        brackets = {'[':']', '{':'}', '(':')', '<':'>', '"':'"', ' ':' '}
        brackets.update({v:k for k, v in self.brackets.items()})

    def __init__(self, line=None, tag=None, value=None, modifiers=None, comment=None, **kwargs):  # TODO kwargs for specific tags
        if line is not None:
            self.parse(line)
            print(self)
            self.validate(warn=True)
        else:
            self.make(tag, value, modifiers, comment, **kwargs)
            self.validate()
        #setattr(self,'__str__', self.___str__)
        #setattr(self,'__repr__', self.___repr__) # apparently __str__ defaults to __repr__ :x

    def make(self, tag, value, modifiers=None, comment=None, **kwargs):
        self.tag = tag
        self.value = value
        self.trailing_modifiers = modifiers
        self.comment = comment
        if tag in self.special_children:
            fields = self.special_children[self.tag][::2]
            for field in fields:
                if field[0] == '*':
                    try:
                        self.__dict__[field[1:]] = kwargs[field[:1]]
                    except KeyError:
                        pass
                else:  # required kwargs
                    self.__dict__[field] = kwargs[field]
        elif tag == 'date':
            if value == None:
                self._value = lambda self: datetime.strfdate(datetime.utcnow(), self._datetime_fmt)
                self.value = property(lambda self: self._value())

        #self.__dict__.update(kwargs)  # just stick the additional kwarsgs in

    def validate(self, warn=False):  # TODO
        if self.tag == 'id':
            if self.value in self._reserved_ids:
                raise AttributeError('You may not use reserved term %s as an id.' % self.value)
        # TODO validate kwargs
        # 
        #warn if we are loading an ontology and there is an error but don't fail
        #id
        #name
        #def
        #synonym
        if not warn:
            print('PLS IMPLMENT ME! ;_;')

    def _value(self):  # FIXME this is super broken :/
        fields = self.special_children[self.tag][::2]
        seps = self.special_children[self.tag][1::2]
        string = ''

        for field, sep in zip(fields, seps):
            if field == 'def':
                embed()
            if sep == ' ':
                extra = ''
            else:
                extra = ' '
            
            try:
                string += extra + sep + self.__dict__[self.esc_(field)] + self.brackets[sep]
            except TypeError:
                string += extra + sep
                string += ', '.join(self.__dict__[self.esc_(field)])
                string += self.brackets[sep]
                #raise
            except KeyError:
                pass

        return string.strip()

    def parse_xrefs(self, *xrefs):  # TODO
        return [xref for xref in xrefs]

    def parse_syno(self, scope_typedef):  # TODO 
        self.__dict__['scope'] = scope_typedef  # FIXME

    def parse_cases(self, value):
        t = self.tag
        if t == 'def':
            text, xrefs = value[1:-1].split('" [')
            self.__dict__['text'] = text
            self.__dict__['xrefs'] = self.parse_xrefs(*xrefs.split(','))
        elif t == 'relationship':
            typedef, term = value.split(' ')
            self.__dict__['typedef'] = typedef
            self.__dict__['target_id'] = term
        elif t == 'synonym':
            text, scope_typedef_xrefs = value[1:-1].split('" ', 1)
            scope_typedef, xrefs = scope_typedef_xrefs.split(' [', 1)
            scope_typedef.strip().rstrip()

            self.__dict__['text'] = text
            self.__dict__['xrefs'] = self.parse_xrefs(*xrefs.split(','))

            if scope_typedef:  # TODO figure out which is which
                try:
                    scope, typedef = scope_typedef.split(' ')
                except ValueError:
                    self.parse_syno(scope_typedef)
                    return
            self.__dict__['scope'] = scope
            self.__dict__['typedef'] = typedef
        elif t == 'xref':  # FIXME busted as hell
            try:
                name, description = value.split(' "', 1)
                description = description[:-1]
            except ValueError:
                name = value
                description = None
            self.__dict__['name'] = name
            self.__dict__['desc'] = description  # opt
        elif t == 'subsetdef':
            name, description = value.split(' "', 1)
            description = description[:-1]
            self.__dict__['name'] = name
            self.__dict__['desc'] = description
        elif t == 'synonymtypedef':
            name, description_scope = value.split(' "', 1)
            description, scope = description_scope.split('"', 1)  # FIXME escapes :/
            scope = scope.strip
            self.__dict__['name'] = name
            self.__dict__['desc'] = description
            self.__dict__['scope'] = scope  # opt  # FIXME defaults
        elif t == 'idspace':
            name, uri_description = value.split(' ', 1)
            uri, description  = uri_description.split(' "')
            description = description[:-1]
            self.__dict__['name'] = name
            self.__dict__['uri'] = uri
            self.__dict__['desc'] = description
        elif t == 'id-mapping':
            id_, target = value.split(' ')
            self.__dict__['id_'] = id_
            self.__dict__['target'] = target
        else:
            raise BaseException('WHAT IS THIS I DONT EVEN')

    def parse(self, line):
        # we will handle extra parse values by sticking them on the tvpair instance
        try:
            tag, value = line.split(':',1)
            self.tag = tag
            value.strip()
            comm_split = value.split('\!')
            try:
                # comment
                tail, comment = comm_split[-1].split('!',1)
                comment = comment.strip()
                comm_split[-1] = tail
                value = '\!'.join(comm_split)
                
            except ValueError:
                comment = None

            value = value.strip()

            # DEAL WITH TRAILING MODIFIERS



            if tag in self.special_children:  # FIXME optional fields ;_;
                self.parse_cases(value)
                self.value = property(lambda self: self._value())
            elif False:
                fields = self.special_children[tag][::2]
                seps = self.special_children[tag][1::2]
                tail = value + ' '  #make the last split clealy
                for sep, field in zip(seps, fields):
                    print('TAIL', tail+'|')
                    if field[0] == '*':
                        field = field[1:]
                        optional = True

                    if sep == ' ':
                        self.__dict__[field], tail = tail.split(self.brackets[sep], 1)
                    else:
                        self.__dict__[field], tail = tail[1:].split(self.brackets[sep], 1)
                        tail = tail.strip()
                    print('WORKING?',self.__dict__[field])
                    tail.strip()  # derp


            else:
                self.value = value.strip().rstrip()
                self._value = lambda : self.value


            #subsetdef: NAME "desc"
            #synonymtypedef: NAME "desc" SCOPE
            #idspace: NAME URI "desc"
            #id-mapping: NAME TARGET

            #def: "definition" [dbxrefs]
            #subset: subsetdef  ! if it is not a subsetdef ParseError it
            #synonym: "name" SCOPE synonymtypedef [xrefs]  ! parse error on no match a std
            #xref: TODO
            #is_a: #XXX we are not going to support all the other crazy stuff
            #intersection_of: ! at least 2
            #union_of: ! at least 2
            #relationship: Typedef.id Term.id
            #is_obsolete: ! true or false
            #replaced_by: ! only if is_obsolete: true
            #consider: ! only if is_obsolete: true

            #dbxref: <name> "<description>" {modifiers}


            """
            # check for quotes  BAD
            if value[0] == '"':
                out = value.split('\\"')
                if len(out) > 1:
                    out[-1], rest = out[-1].split('"')
                    value = '\\"'.join(out)
                else:
                    value, rest = value[1:].split('"', 1)

                if len(rest):  # last expected is []
                    # check for modifiers
                    if rest[-1] == '}':
                        rest, modifiers = rest[-1].split('{', 1)
                        modifiers = eval('dict(' + modifiers + ')')  # danger?
                        rest.rstrip()
                    else:
                        modifiers = {}  # this will make it easier to add stuff later



            else:  # there is only the string value
                self.value = value.rstrip()
                #return




            
            value = value.rstrip()
            if value[-1] == '}':
                value, modifiers = self.brackets(value[:-1])
                modifiers = 'dict(' + modifiers + ')'
                modifiers = eval(modifiers)
            else:
                modifiers = None
            #"""
        except ValueError:
            embed()
            raise

        self.tag = tag
        self.trailing_modifiers = modifiers = None
        self.comment = comment

    def _brackets(self, value, brack='}'):  # XXX
        back = (']','}',')','>')
        if brack in back:
            outside, inside = value.rsplit(self.brackets[brack],1)  # FIXME BAD
        else:
            inside, outside = value.split(match[brack],1)  # FIXME BAD
        if brack in inside:  # too early
            TVPair.brackets(inside)

    def _parse_value(self, value):  # XXX
        if self.tag == 'synonym':
            print('do special synonym stuff')
        elif self.tag == 'def':
            print('split up the []')
        else:
            pass

        return value.strip().rstrip()

    def __str__(self):
        string = '{}: {}'.format(self.tag, self._value())

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
        elif string == 'def':  # avoid syntax errors
            return 'def_'
        return string.replace('-','_').replace(':','')



class TVPairStore:
    def __new__(cls, *args, **kwargs):
        cls._tags = od()
        for tag, limit in cls._all_tags:
            cls._tags[tag] = limit
        cls.__new__ = cls.___new__  # enforce runonce
        return super().__new__(cls)

    @classmethod
    def ___new__(cls, *args, **kwargs):
        return super().__new__(cls)

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
            self._tags[tag] = N
            print(self._tags[tag])
            self.__dict__[dict_tag] = []

        if self._tags[tag] == N:
            self.__dict__[dict_tag].append(tvpair)
        else:
            self.__dict__[dict_tag] = tvpair

    @property
    def tvpairs(self):
        index = tuple(self._tags)

        def key_(tvpair):
            out = index.index(tvpair.tag)
            if self._tags[tvpair.tag] == N:
                tosort = []
                for tvp in self.__dict__[TVPair.esc_(tvpair.tag)]:
                    tosort.append(tvp._value())
                sord = sorted(tosort)
                out += sord.index(tvpair._value()) / (len(sord) + 1)
            return out
            
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
                    print('probably a multipart definition')  # TODO
                    #raise ImportWarning('%s %s is missing a required tag %s' %
                                        #(self.__class__.__name__, str(self), tag))
                else:
                    raise AttributeError('%s must have a tag of type %s' %
                                         (self.__class__.__name__, tag))


class Header(TVPairStore):
    _r_tags = ('format-version', )
    _r_defaults = ('1.2',)
    _all_tags = (
        ('format-version', 1),
        ('data-version', 1),
        ('date', 1),
        ('saved-by', 1),
        ('auto-generated-by', 1),
        ('ontology', 1),
        ('import', N),
        ('subsetdef', N),
        ('synonymtypedef', N),
        ('idspace', N),  # PREFIX http://uri
        ('id-mapping', N),
        ('default-relationship-id-previx', 1),
        ('default-namespace', 1),
        ('remark', N),
    )
    _all_defaults = {
        'date': None,  # autogen at export?
        'saved-by': getuser(),
        'auto-generated-by': __title__,
    }

    def __init__(self, block=None, tvpairs=None):
        super().__init__(block, tvpairs)
        if block is None:
            for tag, default in self._all_defaults.items():
                value = self.__dict__.get(TVPair.esc_(tag), None)
                if value is None:
                    self.__dict__[TVPair.esc_(tag)] = TVPair(tag=tag,value=default)




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
        cls._all_tags = [tag for tag in cls._all_tags if tag[0] not in cls._bad_tags]
        instance = super().__new__(cls, *args, **kwargs)
        cls.__new__ = super().__new__  # enforce runonce
        return instance  # we return here so we chain the runonce

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
    _bad_tags = ['instance_of', 'property_value']
    def __new__(cls, *args, **kwargs):
        cls._bad_tags = cls._typedef_only_tags + cls._typedef_only_tags
        instance = super().__new__(cls, *args, **kwargs)
        cls.__new__ = super().__new__
        return instance


class Typedef(Stanza):
    _bad_tags = ('union_of', 'intersection_of', 'disjoint_from', 'instance_of', 'property_value')


class Instance(Stanza):
    _r_tags = ['instance_of',]
    def __new__(cls, *args, **kwargs):
        cls._bad_tags = cls._typedef_only_tags + cls._typedef_only_tags
        cls._r_tags = super()._r_tags + cls._r_tags
        instance = super().__new__(cls, *args, **kwargs)
        cls.__new__ = super().__new__
        return instance


stanza_types = {type_.__name__:type_ for type_ in (Term, Typedef, Instance)}

def deNone(*args):
    for arg in args:
        if arg == None:
            yield ''
        else:
            yield arg

def main():
    #folder = '/home/tom/ni/protocols/'
    folder = '/home/tgillesp/projects/'
    #folder = 'C:/Users/root/Dropbox/neuroinformatics/protocols/'
    filename = folder + 'ero.obo'
    #filename = folder + 'go.obo'
    #filename = folder + 'ksm_utf8_2.obo'
    of = OboFile(filename=filename)
    print(of)
    embed()

if __name__ == '__main__':
    main()
