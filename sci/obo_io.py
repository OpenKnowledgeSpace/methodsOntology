#!/usr/bin/env python3

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


####
# TODO
# location of ontology tag in header
# relationship missing target_id

"""
    obo_io.py

    python .obo file parser and writer for the obo 1.2 spec defined at
    https://oboformat.googlecode.com/svn/trunk/doc/GO.format.obo-1_2.html
"""
__title__ = 'obo_io'
__author__ = 'Tom Gillespie'
import os
from datetime import datetime
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
            self.Terms = od()
            self.Typedefs = od()
            self.Instances = od()
            self.Headers = od()  #LOL STUPID FIXME
            #od_types = {type_.__name__:type_od for type_,type_od in zip((Term, Typedef, Instance),(self.Terms,self.Typedefs,self.Instances))}
            #LOL GETATTR

            with open(filename, 'rt') as f:
                data = f.read()
            #deal with \<newline> escape
            data = data.replace(' \n','\n')  # FXIME need for arbitrary whitespace
            data = data.replace('\<newline>\n',' ')
            sections = data.split('\n[')
            header_block = sections[0]
            self.header = Header(header_block, self)
            stanzas = sections[1:]
            for block in stanzas:
                block_type, block = block.split(']\n',1)
                type_ = stanza_types[block_type]
                #odt = od_type[block_type]
                type_(block, self)#, type_od=odt)

            self.Terms.names = {}
            for id_, term in self.Terms.items():  # TODO for nonparse
                if term.name.value not in self.Terms.names:
                    self.Terms.names[term.name.value] = term
                elif type(self.Terms.names[term.name.value]) == list:
                    self.Terms.names[term.name.value].append(term)
                else:
                    existing = self.Terms.names.pop(term.name.value)
                    self.Terms.names[term.name.value] = [existing, term]
        else:
            self.header = header
            self.Terms = terms  # TODO this should take iters not ods
            self.Typedefs = typedefs
            self.Instances = instances

    def write(self, filename):  #FIXME this is bugged
        if os.path.exists(filename):
            name, ext = filename.rsplit('.',1)
            try:
                prefix, num = name.rsplit('_',1)
                n = int(num)
                n += 1
                filename = prefix + '_' + str(n) + '.' + ext
            except ValueError:
                filename = name + '_1.' + ext
            print('file exists, renaming to %s' % filename)
            self.write(filename)

        else:
            with open(filename, 'wt') as f:
                f.write(str(self))  # FIXME this is incredibly slow for big files :/

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
        ('synonym', ('text', '"', '*scope', ' ', '*typedef', ' ', 'xrefs', '[')),
        ('xref', ('name', ' ', '*desc', '"')),
        ('relationship', ('typedef', ' ', 'target_id', ' ')),

        ('property_value', ('type_id', ' ', 'val', ' ', '*datatype', ' ')),  # WAT
    )
    special_children = {k:v for k, v in special_children}

    brackets = {'[':']', '{':'}', '(':')', '<':'>', '"':'"', ' ':' '}
    brackets.update({v:k for k, v in brackets.items()})

    def __init__(self, line=None, tag=None, value=None, modifiers=None, comment=None, type_od=None, **kwargs):  # TODO kwargs for specific tags
        if type_od:
            self.type_od = type_od

        if line is not None:
            self.parse(line)
            #print(self)
            self.validate(warn=True)
        else:
            self.make(tag, value, modifiers, comment, **kwargs)
            self.validate()

    @staticmethod
    def factory(tag, value=None, modifiers=None, comment=None, dict_=None, **kwargs):
        tvp = TVPair(tag=tag, value=value, modifiers=None, comment=None, **kwargs)
        if dict_:
            dict_[TVPair.esc_(tag)] = tvp
        else:
            return tvp

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

    def _value(self):
        return self.value

    def __value(self):  # FIXME this is super broken :/
        fields = self.special_children[self.tag][::2]
        seps = self.special_children[self.tag][1::2]
        string = ''

        for field, sep in zip(fields, seps):
            if sep == ' ':
                extra = ''
            else:
                extra = ' '

            if field[0] == '*':
                field = field[1:]
                if not self.__dict__[self.esc_(field)]:
                    continue
            
            try:
                value = self.__dict__[self.esc_(field)]
            except KeyError:
                embed()
                raise

            if type(value) == str:
                string += extra + sep + value
                if sep != ' ':
                    string += self.brackets[sep]  # prevent double spaces
            elif type(value) == list:
                if sep != '[':
                    raise TypeError('um what? lists should be bracketed?!')
                string += extra + sep
                string += ', '.join(value)
                string += self.brackets[sep]
            else:
                embed()
                raise TypeError('wtf you giving me?')

        return string.strip()

    def parse_xrefs(self, *xrefs):  # TODO
        return [xref.strip().rstrip() for xref in xrefs]

    def parse_syno(self, scope_typedef):  # TODO 
        self.__dict__['scope'] = scope_typedef  # FIXME
        self.__dict__['typedef'] = None

    def parse_cases(self, value):  # TODO define the subfield names in one place
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
        elif t == 'property_value':
            type_id, val_datatype = value.split(' ', 1)
            try:
                val, datatype = val_datatype.split(' ', 1)
            except ValueError:
                val = val_datatype
                datatype = None
            self.__dict__['type_id'] = type_id
            self.__dict__['val'] = val
            self.__dict__['datatype'] = datatype
        elif t == 'subsetdef':
            name, description = value.split(' "', 1)
            description = description[:-1]
            self.__dict__['name'] = name
            self.__dict__['desc'] = description
        elif t == 'synonymtypedef':
            name, description_scope = value.split(' "', 1)
            description, scope = description_scope.split('"', 1)  # FIXME escapes :/
            scope = scope.strip()
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
            trailing_modifiers = None

            if tag in self.special_children:  # FIXME optional fields ;_;
                self.parse_cases(value)
                self._value = self.__value
                self.value = property(lambda self: self._value())
                self.comment = comment

            elif tag == 'is_a':
                def _is_a_callback(target):  # TODO errors and dangling
                    self.__dict__['target'] = target
                self.__dict__['target'] = 'DANGLING'
                test = self.type_od.get(value, None)
                if type(test) == list:  # multiple things will need to callback
                    self.type_od[value].append(_is_a_callback)
                elif test is None:
                    self.type_od[value] = [_is_a_callback]
                else:  # its a Term or something
                    self.__dict__['target'] = test

                    
                self._value = self._is_a_value
                self._comment = self._is_a_comment
                self.value = property(self._value)
                self.comment = property(self._comment)
            else:
                self.value = value.strip().rstrip()
                self.comment = comment
                #self._value already default

        except BaseException as e:
            embed()
            raise 

        self.tag = tag
        self.trailing_modifiers = trailing_modifiers


    def _is_a_value(self):
        return self.target.id_.value

    def _is_a_comment(self):
        return self.target.name.value

    def _comment(self):
        return self.comment

    def make(self, tag, value=None, modifiers=None, comment=None, **kwargs):
        """ special children should use **kwargs on subfields instead of values
            we should probably define those somewhere, maybe even as their own
            classes in some future implementation??? a class Value or something
        """
        self.tag = tag
        self.trailing_modifiers = modifiers
        self.comment = comment
        if tag in self.special_children:
            fields = self.special_children[self.tag][::2]
            for field in fields:
                if field[0] == '*':  # optional kwargs
                    try:
                        self.__dict__[field[1:]] = kwargs[field[:1]]
                    except KeyError:
                        pass
                else:  # required kwargs
                    self.__dict__[field] = kwargs[field]
            self._value = self.__value
            self.value = property(self._value)
        else:
            self.value = value
            #self._value is already efault for this case

    def __eq__(self, other):
        if type(self) == type(other):
            if self.value == other.value:
                return True
            else:
                return False
        else:
            return False

    def __ne__(self, other):
        return not other == self

    def __str__(self):
        string = '{}: {}'.format(self.tag, self._value())

        if self.trailing_modifiers:
            string += " " + str(self.trailing_modifiers)

        if self.comment:
            # TODO: autofill is_a comments
            string += " ! " + self._comment()

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

    def __init__(self, block=None, obofile=None, tvpairs=None):
        # keep _tags out of self.__dict__ and add new tags for all instances
        if obofile is not None:
            type_od = getattr(obofile, self.__class__.__name__+'s')
        else:
            raise TypeError('TVPairStores need an OboFile, even if it is a fake one.')  # FIXME just don't check stuff instead?

        for tag, limit in self._tags.items():
            if limit == N:
                self.__dict__[TVPair.esc_(tag)] = []  # may need a list

        if block is not None:
            lines = block.split('\n')
            for line in lines:
                if line:
                    tvpair = TVPair(line, type_od=type_od)
                    self.add_tvpair(tvpair)
            warn = True
        else:
            for tvpair in tvpairs:  # FIXME, sorta need a way to get the type_od to them more naturally?
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

        if tag not in self.__dict__:
            if tag not in self._tags:
                print('TAG NOT IN', tag)
                self._tags[tag] = N
                print(self._tags[tag])
                self.__dict__[dict_tag] = []
            elif self._tags[tag] == N:
                self.__dict__[dict_tag] = []

        if self._tags[tag] == N:
            try:
                self.__dict__[dict_tag].append(tvpair)
            except KeyError:
                embed()
                raise
        else:
            self.__dict__[dict_tag] = tvpair

    @property
    def tvpairs(self):
        return self._tvpairs()

    def _tvpairs(self, source_dict=None):
        index = tuple(self._tags)

        def key_(tvpair):
            out = index.index(tvpair.tag)
            if self._tags[tvpair.tag] == N:
                tosort = []
                for tvp in self.__dict__[TVPair.esc_(tvpair.tag)]:
                    tosort.append(tvp._value())
                sord = sorted(tosort, key=lambda a: a.lower())  # FIXME isn't quit right
                out += sord.index(tvpair._value()) / (len(sord) + 1)
            return out
            
        tosort = []
        if not source_dict:
            source_dict = self.__dict__
        for tvp in source_dict.values():
            if type(tvp) == list:
                tosort.extend(tvp)
            elif type(tvp) == property:
                embed()
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
    _datetime_fmt = '%d:%m:%Y %H:%M'  # WE USE ZULU

    def __str__(self):
        """ When we write to file overwrite the relevant variables without
            also overwriting the original data.
        """
        updated = {k:v for k, v in self.__dict__.items()}
        print(updated.keys())
        TVPair.factory('date', datetime.strftime(datetime.utcnow(), self._datetime_fmt),dict_=updated)
        TVPair.factory('auto-generated-by', __title__, dict_=updated)
        TVPair.factory('saved-by', getuser(), dict_=updated)
        tvpairs = self._tvpairs(updated)
        return '\n'.join(str(tvpair) for tvpair in tvpairs) + '\n'


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
        ('domain', 1), #
        ('range', 1), #
        ('is_anti_symmetric', 1), #
        ('is_cyclic', 1), #
        ('is_reflexive', 1), #
        ('is_symmetric', 1), #
        ('is_transitive', 1), #
        ('is_a', N),
        ('inverse_of', 1), #
        ('transitive_over', N), #
        ('intersection_of', N),  # no relationships, typedefs
        ('union_of', N),  # min 2, no relationships, typedefs
        ('disjoint_from', N),  # no relationships, typedefs
        ('relationship', N),
        ('property_value', N), ##
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
            super().__init__(block, obofile)
        else:
            super().__init__(tvpairs=tvpairs)

        type_od = getattr(obofile, self.__class__.__name__+'s')
        callbacks = type_od.get(self.id_.value, None)
        if type(callbacks) == list:
            for callback in callbacks:
                print('callback set',self)
                callback(self)  # fill in is_a
            type_od.pop(self.id_.value)  # reset the order
        type_od[self.id_.value] = self  # atm we need names
        type_od.__dict__[TVPair.esc_(self.id_.value)] = self

    def __str__(self):
        return '['+ self.__class__.__name__ +']\n' + super().__str__()


class Term(Stanza):
    _bad_tags = ['instance_of']
    def __new__(cls, *args, **kwargs):
        cls._bad_tags += cls._typedef_only_tags
        instance = super().__new__(cls, *args, **kwargs)
        cls.__new__ = super().__new__
        return instance


class Typedef(Stanza):
    _bad_tags = ('union_of', 'intersection_of', 'disjoint_from', 'instance_of')


class Instance(Stanza):
    _r_tags = ['instance_of',]
    def __new__(cls, *args, **kwargs):
        cls._bad_tags += cls._typedef_only_tags
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

__all__ = [OboFile.__name__, TVPair.__name__, Header.__name__, Term.__name__, Typedef.__name__, Instance.__name__]

def main():
    folder = '/home/tom/ni/protocols/'
    #folder = '/home/tgillesp/projects/'
    #folder = 'C:/Users/root/Dropbox/neuroinformatics/protocols/'
    #filename = folder + 'ero.obo'
    #filename = folder + 'badobo.obo'
    filename = folder + 'ksm_utf8_2.obo'
    of = OboFile(filename=filename)
    #print(of)
    embed()

if __name__ == '__main__':
    main()
