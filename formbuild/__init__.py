# -*- coding: utf-8 -*-

"""\
Build HTML forms
"""

import logging
import re
import sys

if sys.version_info < (3,):
  from cgi import escape
else:
  import html
  from html import escape
from markupsafe import Markup
from bn import HTMLFragment

log = logging.getLogger(__name__)

try:
    from collections import OrderedDict
except ImportError: # Python 2.5 and below
    ## {{{ http://code.activestate.com/recipes/576693/ (r6)
    from UserDict import DictMixin

    class OrderedDict(dict, DictMixin):

        def __init__(self, *args, **kwds):
            if len(args) > 1:
                raise TypeError('expected at most 1 arguments, got %d' % len(args))
            try:
                self.__end
            except AttributeError:
                self.clear()
            self.update(*args, **kwds)

        def clear(self):
            self.__end = end = []
            end += [None, end, end]         # sentinel node for doubly linked list
            self.__map = {}                 # key --> [key, prev, next]
            dict.clear(self)

        def __setitem__(self, key, value):
            if key not in self:
                end = self.__end
                curr = end[1]
                curr[2] = end[1] = self.__map[key] = [key, curr, end]
            dict.__setitem__(self, key, value)

        def __delitem__(self, key):
            dict.__delitem__(self, key)
            key, prev, next = self.__map.pop(key)
            prev[2] = next
            next[1] = prev

        def __iter__(self):
            end = self.__end
            curr = end[2]
            while curr is not end:
                yield curr[0]
                curr = curr[2]

        def __reversed__(self):
            end = self.__end
            curr = end[1]
            while curr is not end:
                yield curr[0]
                curr = curr[1]

        def popitem(self, last=True):
            if not self:
                raise KeyError('dictionary is empty')
            if last:
                key = reversed(self).next()
            else:
                key = iter(self).next()
            value = self.pop(key)
            return key, value

        def __reduce__(self):
            items = [[k, self[k]] for k in self]
            tmp = self.__map, self.__end
            del self.__map, self.__end
            inst_dict = vars(self).copy()
            self.__map, self.__end = tmp
            if inst_dict:
                return (self.__class__, (items,), inst_dict)
            return self.__class__, (items,)

        def keys(self):
            return list(self)

        setdefault = DictMixin.setdefault
        update = DictMixin.update
        pop = DictMixin.pop
        values = DictMixin.values
        items = DictMixin.items
        iterkeys = DictMixin.iterkeys
        itervalues = DictMixin.itervalues
        iteritems = DictMixin.iteritems

        def __repr__(self):
            if not self:
                return '%s()' % (self.__class__.__name__,)
            return '%s(%r)' % (self.__class__.__name__, self.items())

        def copy(self):
            return self.__class__(self)

        @classmethod
        def fromkeys(cls, iterable, value=None):
            d = cls()
            for key in iterable:
                d[key] = value
            return d

        def __eq__(self, other):
            if isinstance(other, OrderedDict):
                return len(self)==len(other) and self.items() == other.items()
            return dict.__eq__(self, other)

        def __ne__(self, other):
            return not self == other
    ## end of http://code.activestate.com/recipes/576693/ }}}

class XHTMLBuilder(object):
    close = Markup('/>')

    def html_open(self, name, close, attributes=None):
        """\
        Returns an HTML open tag for ``name`` with everything properly escaped.
        """
        fragment = Markup('<')+name
        if attributes is not None:
            for k, v in attributes.items():
                fragment += (Markup(' %s="%s"')%(k, v))
        if close and self.close:
            fragment += (Markup(" %s")%self.close)
        else:
            fragment += Markup(">")
        return fragment

    def html_close(self, name):
        """\
        Returns an HTML close tag for ``name``
        """
        return Markup('</%s>')%(name,)

class HTMLBuilder(XHTMLBuilder):
    close = None

def check_attributes(attributes, to_exclude):
    if attributes is None:
        return {}
    final = OrderedDict()
    attribute_keys = []
    for key in attributes:
        if not isinstance(key, unicode):
            try:
                attribute_keys.append(unicode(key.lower()))
            except:
                raise Exception('Attribute keys should be unicode values, so %r is an invalid value'%key)
        else:
            attribute_keys.append(key.lower())
        if isinstance(attributes[key], (int, long)):
            final[key] = Markup(attributes[key])
        elif not isinstance(attributes[key], unicode):
            try:
                final[key] = unicode(attributes[key])
            except:
                raise Exception('Attribute values should be unicode values, so %r is an invalid value'%attributes[key])
        else:
            final[key] = attributes[key]
    for attribute in to_exclude:
        if attribute in attribute_keys:
            raise Exception(
                "You cannot directly specify %r as a field attribute, "
                "instead use the correct API for the field you are trying "
                "to create" % (
                    attribute,
                )
            )
    return final

def _handle_input(type, name, value, attributes, builder):
    attributes = check_attributes(attributes, ['type', 'name', 'value'])
    attributes.update(
        dict(
            type=type,
            name=name,
        )
    )
    if value is not None:
        attributes['value'] = value
    return builder.html_open('input', True, attributes)

def _split(name):
    parsed_options = []
    for part in name.split('.'):
        parts = part.split('[')
        name = parts[0]
        number = None
        if len(parts):
            number = parts[1].replace(']', '')
        parsed_options.append((name, number))
    return parsed_options

def group(
    name,
    selected_values,
    options,
    group_type,
    align='horiz',
    cols=4,
    sub_name=None,
    builder=None
):
    if builder is None:
        builder = XHTMLBuilder()
    if not group_type in ['checkbox', 'radio']:
        raise Exception('Invalid group type %s'%group_type)
    if selected_values is None:
        raise Exception(selected_values)
    fragment = HTMLFragment()
    item_counter = 0
    if len(options) > 0:
        if align != 'table':
            for option in options:
                v = option['id']
                k = option['label']
                checked=u''
                # This isn't a good enough check
                if unicode(v) in selected_values:
                    checked=' checked="checked"'
                break_ = u'\n'
                if align == 'vert':
                    break_='<br />\n'#builder.html_open('br', close=True)+'\n'
                fragment.safe('<input type="')
                # It was checked earlier, so it is safe
                fragment.safe(group_type)
                fragment.safe('" name="')
                if sub_name:
                    fragment.write(name)
                    fragment.safe('[%s].'%(item_counter))
                    fragment.write(sub_name)
                else:
                    fragment.write(name)
                fragment.safe('" value="')
                fragment.write(unicode(v))
                fragment.safe('"'+checked+' /> ')
                fragment.write(unicode(k))
                fragment.safe(break_)
                item_counter += 1
        else:
            fragment.safe(
                u'<table border="0" width="100%" cellpadding="0" '
                u'cellspacing="0">\n    <tr>\n'
            )
            counter = -1
            for option in options:
                counter += 1
                if ((counter % cols) == 0) and (counter != 0):
                    fragment.safe(u'    </tr>\n    <tr>\n')
                fragment.safe('      <td>')
                checked=u''
                align=u''
                v = option['id']
                k = option['label']
                if unicode(v) in selected_values:
                    checked=' checked="checked"'
                break_ = u'</td>\n      <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>\n'
                fragment.safe('<input type="')
                # It was checked earlier, so it is safe
                fragment.safe(group_type)
                fragment.safe('" name="')
                if sub_name:
                    fragment.write(name)
                    fragment.safe('[%s].'%(item_counter))
                    fragment.write(sub_name)
                else:
                    fragment.write(name)
                fragment.safe('" value="')
                fragment.write(unicode(v))
                fragment.safe('"'+checked+' /> ')
                fragment.write(unicode(k))
                fragment.safe(break_)
                item_counter += 1
            counter += 1
            while (counter % cols):
                counter += 1
                fragment.safe(
		    u'      <td></td>\n      '
		    u'<td>&nbsp;&nbsp;&nbsp;&nbsp;</td>\n'
		)
            fragment.safe(u'    </tr>\n</table>\n')
    return Markup(fragment.getvalue()[:-1])

def _checkable(checked, type, name, value, attributes=None, builder=None):
    if builder is None:
        builder = XHTMLBuilder()
    attributes = check_attributes(
        attributes,
        ['type', 'name', 'checked', 'value'],
    )
    attributes.update(
        dict(
            type=type,
            name=name,
            value=value,
        )
    )
    if checked.get(name, False) is True:
        attributes['checked'] = u'checked'
    return builder.html_open('input', True, attributes)

def _select(
    value,
    options,
    multiple,
    name,
    attributes=None,
    get_option_attributes=None,
    self=None,
):
    """\
    Private method for generating ``<select>`` fields.

    You should use ``dropdown()`` for single value selects or ``combo()``
    for multi-value selects.
    """
    attributes = check_attributes(attributes, ['name', 'multiple'])
    if multiple:
        attributes['multiple'] = 'multiple'
    attributes['name'] = name
    fragment = Markup(u'')
    fragment += self.builder.html_open(u'select', False, attributes)+Markup(u'\n')
    counter = 0
    for option in options:
        v = option['id']
        k = option['label']
        if get_option_attributes:
            option_attr = get_option_attributes(self, v, k)
        else:
            option_attr = {}
        option_attr = check_attributes(option_attr, ['value', 'selected'])
        if unicode(v) in value:
            option_attr['selected'] = 'selected'
        option_attr['value'] = v
        fragment += self.builder.html_open(u'option', False, option_attr)
        fragment += k
        fragment += self.builder.html_close('option')+Markup(u'\n')
    fragment += self.builder.html_close('select')
    return fragment

class Field(object):
    def __init__(
        self,
        value=None,
        option=None,
        checked=None,
        builder=None,
    ):
        """\
        ``value``
            a dictionary of field values where the name represents the field name and
            the value is a Unicode string representing the field value.

        ``option``
            an iterable of ``(value, label)`` pairs. The value is what's returned to
            the application if this option is chosen; the label is what's shown in the
            form. You can also pass an iterable of strings in which case the labels will
            be identical to the values.

        ``checked``
            a dictionary where the keys are field names and the values are ``True`` or
            ``False`` depending on whether the box should be checked or not. The value
            of a checked checkbox comes from the ``value`` argument. Checkbox groups
            are handled differently, so this argument only applies to single checkboxes.

        ``builder``
           a custom HTML builder to use. Defaults to ``XHTMLBuilder`` if not specified.
        """
        self.builder = builder or XHTMLBuilder()
        _ensure_flat_and_set(self, 'value', value)
        option_final = {}
        if option is not None:
            if not isinstance(option, dict):
                raise Exception("Expected the 'option' argument to be a dictionary")
            else:
                for k in option:
                    options = []
                    if not isinstance(option[k], (list, tuple)):
                        raise Exception("Expected the value of the 'option' argument's %r key to be a list or tuple of dictionaries"%(k,))
                    for i, item in enumerate(option[k]):
                        if not isinstance(item, dict):
                            error = (
                                "Expected item %s in the list of options for the "
                                "%r field to be a dictionary not %s with value "
                                "%s..." % (
                                    i,
                                    k,
                                    str(type(item))[1:-1],
                                    item,
                                )
                            )
                            if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], (str, unicode)) and isinstance(item[1], (str, unicode)):

                                log.warning(error+'. Converting to a dict')
                                options.append({u'id': item[0], u'label': item[1]})
                            else:
                                raise Exception(error)
                        else:
                            for key in ['id', 'label']:
                                if not item.has_key(key):
                                    raise Exception("Expected item %s in the list of options for the %r field to be dictionary with a key named %r"%(i, k, key))
                                if not isinstance(item[key], unicode):
                                    raise Exception("Expected item %s in the list of options for the %r field to be dictionary where the key named %r has a value which is a unicode string, not %r"%(i, k, key, item[key]))
                            options.append(item)
                    option_final[k] = options
            self.option = option_final
        else:
            self.option = {}
        if checked is not None:
            if not isinstance(checked, dict):
                raise Exception("Expected the 'checked' argument to be a dictionary")
            else:
                for k in checked:
                    if not isinstance(checked[k], bool):
                        raise Exception("Expected the values of the 'checked' argument to be True or False, but the %s key has a value %s"%(k, checked[k]))
            self.checked = checked
        else:
            self.checked = {}

    #
    # Single value fields
    #

    def password(self, name=u"password", attributes=None, populate=True):
        """\
        Creates a password field

        ``name``
            Defaults to ``password``.

        >>> field = Field(value=dict(name=u'James>'))
        >>> print field.password(u'name')
        <input type="password" name="name" value="James&gt;" />
        >>> print field.password(u'name', populate=False)
        <input type="password" name="name" value="" />
        """
        return _handle_input(
            'password',
            name,
            populate and self.value.get(name) or u'',
            attributes,
            self.builder,
        )

    def hidden(self, name, attributes=None):
        """\
        Creates a hidden field.

        Note: You can also add hidden fields to a ``Form`` instance in the ``end()`` or
        ``end_with_layout()`` fields by specifying the names of the all the
        hidden fields you want added.

        >>> field = Field(value=dict(name=u'value'))
        >>> print field.hidden(u'name')
        <input type="hidden" name="name" value="value" />
        """
        return _handle_input(
            'hidden',
            name,
            self.value.get(name),
            attributes,
            self.builder,
        )

    def text(self, name, attributes=None):
        """\
        Create a text input field.

        >>> field = Field()
        >>> print field.text('name')
        <input type="text" name="name" />
        >>> field = Field(value=dict(name=u'James>'))
        >>> print field.text('name')
        <input type="text" name="name" value="James&gt;" />
        """
        return _handle_input(
            'text',
            name,
            self.value.get(name),
            attributes,
            self.builder,
        )

    def textarea(self, name, attributes=None):
        """\
        Creates a textarea field.

        >>> field = Field(value=dict(name=u'James>'))
        >>> print field.textarea('name')
        <textarea name="name">James&gt;</textarea>
        """
        attributes = check_attributes(attributes, ['name'])
        attributes["name"] = name
        return self.builder.html_open('textarea', False, attributes)+\
           (self.value.get(name) or u'')+self.builder.html_close(u'textarea')

    #
    # Zero Value fields
    #

    def static(self, name):
      """\
      Return the static value instead of an HTML field.
      >>> field = Field(value=dict(name=u'James>'))
      >>> print field.static('name')
      James&gt;
      """
      value = self.value.get(name)
      if sys.version_info < (3,):
        ValueReturn=escape(unicode(value))
      else:
        ValueReturn=escape( value, quote=False )
      return ValueReturn

    def file(self, name, attributes=None):
        """\
        Creates a file upload field.

        If you are using file uploads then you will also need to set the
        form's ``enctype`` attribute to ``"multipart/form-data"`` and
        ensure the ``method`` attribute is set to ``POST``.

        Example:

        >>> field = Field()
        >>> print field.file('myfile')
        <input type="file" name="myfile" />

        Note: File fields cannot have a ``value`` attribute.
        """
        return _handle_input(
            'file',
            name,
            None,
            attributes,
            self.builder,
        )

    #
    # Single value fields with read-only values set at desgin time
    #

    def image_button(self, name, value, src, alt=None, attributes=None):
        """\
        Create a submit button with an image background

        ``value``
            The value of the field. Also used as the ``alt`` text if ``alt``
            is not also specified.

        ``src``
            The URL of the image to use as the button

        ``alt``
            The text to use as the alt text

        >>> field = Field()
        >>> print field.image_button('go', 'Next', '../go.png', alt='Go')
        <input src="../go.png" alt="Go" type="image" name="go" value="Next" />
        """
        if alt is None:
            alt=value
        attributes = check_attributes(
            attributes,
            ['type', 'name', 'value', 'src', 'alt']
        )
        attributes.update(
            dict(
                type='image',
                name=name,
                value=value,
                src=src,
                alt=alt,
            )
        )
        return self.builder.html_open('input', True, attributes)

    def submit(self, name='sumbit', value='Submit', attributes=None):
        """\
        Creates a submit button with the text ``<tt>value</tt>`` as the
        caption.

        >>> field = Field()
        >>> print field.submit(u'name', u'Submit >')
        <input type="submit" name="name" value="Submit &gt;" />
        """
        return _handle_input(
            'submit',
            name,
            value,
            attributes,
            self.builder,
        )

    #
    # Single value fields whose value is set at constuct time but should not
    # be allowed to change
    #

    def checkbox(self, name, value, attributes=None):
        """\
        Creates a check box.

        >>> field = Field()
        >>> print field.checkbox('name', 'James >')
        <input type="checkbox" name="name" value="James &gt;" />
        >>> field = Field(value={u'name': u'Set at runtime'})
        >>> print field.checkbox(u'name', u'Set at design time')
        <input type="checkbox" name="name" value="Set at design time" />
        >>> field = Field(checked={'name': True})
        >>> print field.checkbox('name', 'J>')
        <input checked="checked" type="checkbox" name="name" value="J&gt;" />
        """
        return _checkable(self.checked, 'checkbox', name, value, attributes, self.builder)

    def radio(self, name, value, attributes=None):
        """\
        Creates a radio button.

        >>> field = Field()
        >>> print field.radio('name', 'James >')
        <input type="radio" name="name" value="James &gt;" />
        >>> field = Field(value={u'name': u'Set at runtime'})
        >>> print field.radio(u'name', u'Set at design time')
        <input type="radio" name="name" value="Set at design time" />
        >>> field = Field(checked={'name': True})
        >>> print field.radio('name', 'J>')
        <input checked="checked" type="radio" name="name" value="J&gt;" />
        """
        return _checkable(self.checked, 'radio', name, value, attributes, self.builder)

    #
    # Single value fields with options
    #

    def dropdown(self, name, option=None, attributes=None, get_option_attributes=None):
        """\
        Create a single-valued <select> field

        >>> field = Field(
        ...     value={u'fruit': u'1'},
        ...     option={
        ...         u'fruit': [
        ...             (u'1', u'Bananas'),
        ...             (u'2>', u'Apples <>'),
        ...             (u'3', u'Pears'),
        ...         ]
        ...     }
        ... )
        >>> print field.dropdown('fruit')
        <select name="fruit">
        <option selected="selected" value="1">Bananas</option>
        <option value="2&gt;">Apples &lt;&gt;</option>
        <option value="3">Pears</option>
        </select>

        If not options for the select field are specified in the ``Field``
        constructor, no options will be rendered:

        >>> field = Field(
        ...     value={u'fruit': u'1'},
        ...     option={}
        ... )
        >>> print field.dropdown(u'fruit')
        <select name="fruit">
        </select>

        Create a single-valued <select> field from nested data with shared options

        >>> field = Field(
        ...     value={u'fruit[0].id': u'1', u'fruit[1].id': u'3'},
        ...     option={
        ...         u'fruit[*].id': [
        ...             (u'1', u'Bananas'),
        ...             (u'2>', u'Apples <>'),
        ...             (u'3', u'Pears'),
        ...         ]
        ...     }
        ... )
        >>> print field.dropdown('fruit[0].id')
        <select name="fruit[0].id">
        <option selected="selected" value="1">Bananas</option>
        <option value="2&gt;">Apples &lt;&gt;</option>
        <option value="3">Pears</option>
        </select>
        >>> print field.dropdown('fruit[1].id')
        <select name="fruit[1].id">
        <option value="1">Bananas</option>
        <option value="2&gt;">Apples &lt;&gt;</option>
        <option selected="selected" value="3">Pears</option>
        </select>
        """
        value = self.value.get(name, u'')
        if '.' in name or '[' in name:
            parts = name.split('.')
            name_ = '.'.join(parts[:-1])
            sub_name = parts[-1]
            real_option = _get_option(self, option, name_, sub_name=sub_name)
        else:
            real_option = self.option.get(name, [])
        if not isinstance(value, (str, unicode)):
            raise Exception(
                'The value for a dropdown should be a unicode '
                'string, not %r'%(
                    type(value),
                )
            )
        return _select(self.value.get(name, []), real_option, False, name, attributes, get_option_attributes, self)

    def radio_group(self, name, option=None, align='horiz', cols=4, sub_name=None):
        """Radio Group Field.

        ``value``
            The value of the selected option, or ``None`` if no radio button
            is selected

        ``align``
            can be ``'horiz'`` (default), ``'vert'`` or ``table``. If table layout is
            chosen then you can also use the ``cols`` argument to specify the number
            of columns in the table, the default is 4.

        Examples (deliberately including some '>' characters to check they are properly escaped)

        >>> field = Field(
        ...     value={u'fruit': u'1'},
        ...     option={
        ...         u'fruit': [
        ...             (u'1', u'Bananas'),
        ...             (u'2>', u'Apples <>'),
        ...             (u'3', u'Pears'),
        ...         ]
        ...     }
        ... )
        >>> print field.radio_group('fruit')
        <input type="radio" name="fruit" value="1" checked="checked" /> Bananas
        <input type="radio" name="fruit" value="2&gt;" /> Apples &lt;&gt;
        <input type="radio" name="fruit" value="3" /> Pears
        >>> print field.radio_group('fruit', align='vert')
        <input type="radio" name="fruit" value="1" checked="checked" /> Bananas<br />
        <input type="radio" name="fruit" value="2&gt;" /> Apples &lt;&gt;<br />
        <input type="radio" name="fruit" value="3" /> Pears<br />
        >>> print field.radio_group('fruit', align='table', cols=2)
        <table border="0" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td><input type="radio" name="fruit" value="1" checked="checked" /> Bananas</td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
              <td><input type="radio" name="fruit" value="2&gt;" /> Apples &lt;&gt;</td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            </tr>
            <tr>
              <td><input type="radio" name="fruit" value="3" /> Pears</td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
              <td></td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            </tr>
        </table>

        If no options are present in the ``Field`` constructor, none will be
        rendered:

        >>> field = Field(
        ...     value={u'fruit': u'1'},
        ...     option={}
        ... )
        >>> field.radio_group('fruit')
        Markup(u'')
        >>> field.radio_group('fruit', align='table')
        Markup(u'')

        Here's an example with nested variables:

        >>> field = Field(
        ...     value={u'fruit[0].id': u'1'},
        ...     option={
        ...         u'fruit[*].id': [
        ...             (u'1', u'Bananas'),
        ...             (u'2>', u'Apples <>'),
        ...             (u'3', u'Pears'),
        ...         ]
        ...     }
        ... )
        >>> print field.radio_group('fruit[0].id')
        <input type="radio" name="fruit[0].id" value="1" checked="checked" /> Bananas
        <input type="radio" name="fruit[1].id" value="2&gt;" /> Apples &lt;&gt;
        <input type="radio" name="fruit[2].id" value="3" /> Pears
        """
        if '.' in name or '[' in name:
            parts = name.split('.')
            name_ = '['.join('.'.join(parts[:-1]).split('[')[:-1])
            sub_name = parts[-1]
            real_option = _get_option(self, option, name_, sub_name=sub_name)
        else:
            name_ = name
            real_option = self.option.get(name, [])
        if self.value.get(name, []):
            selected_values = [self.value[name]]
        else:
            selected_values = []
        return group(
            name_,
            selected_values,
            real_option,
            'radio',
            align,
            cols,
            sub_name
        )

    #
    # Multi-valued fields
    #

    def combo(self, name, attributes=None, sub_name=None, get_option_attributes=None):
        """\
        Create a multi-valued <select> field

        >>> field = Field(
        ...     value={u'fruit[0].id': u'1', u'fruit[1].id': u'3'},
        ...     option={
        ...         u'fruit[*].id': [
        ...             (u'1', u'Bananas'),
        ...             (u'2>', u'Apples <>'),
        ...             (u'3', u'Pears'),
        ...         ]}
        ... )
        >>> print field.combo('fruit', sub_name='id')
        <select multiple="multiple" name="fruit">
        <option selected="selected" value="1">Bananas</option>
        <option value="2&gt;">Apples &lt;&gt;</option>
        <option selected="selected" value="3">Pears</option>
        </select>

        If not options for the select field are specified in the ``Field``
        constructor, no options will be rendered:

        >>> field = Field(
        ...     value={u'fruit[0].id': u'1', u'fruit[1].id': u'3'},
        ...     option={}
        ... )
        >>> print field.combo('fruit', sub_name='id')
        <select multiple="multiple" name="fruit">
        </select>

	Note that a combo box submits multiple values for the same field name
        so is tricky to handle because it doesn't fit a NORM model (see docs for a
        definition). Instead it is recommended you use a multi-value autocomplete field
        if there are lots of options or a checkbox group if there aren't too many.
        """
        if not sub_name:
            raise Exception('No sub_name specified')
        selected_values = []
        for k, v in self.value.items():
            if k.startswith(name+'[') and k.endswith('].'+sub_name):
                selected_values.append(v)
        return _select(
            selected_values,
            #self.option.get(name, []),
            _get_option(self, None, name, sub_name),
            True,
            name,
            attributes,
            get_option_attributes,
            self,
        )

    def checkbox_group(self, name, align='horiz', cols=4, sub_name=None):
        """Check Box Group Field.

        ``align``
            can be ``'horiz'`` (default), ``'vert'`` or ``table``. If table layout is
            chosen then you can also use the ``cols`` argument to specify the number
            of columns in the table, the default is 4.

        Examples (deliberately including some '>' characters to check they are properly escaped)

        If no options are present in the ``Field`` constructor, none will be
        rendered:

        >>> field = Field(
        ...     value={
        ...         u'fruit[0].id': u'1',
        ...         u'fruit[1].id': u'3',
        ...     },
        ...     option={}
        ... )
        >>> field.checkbox_group('fruit', sub_name='id')
        Markup(u'')

        Let's have some values:

        >>> field = Field(
        ...     value={u'fruit[0].id': u'1', u'fruit[1].id': u'3'},
        ...     option={
        ...         u'fruit[*].id': [
        ...             (u'1', u'Bananas'),
        ...             (u'2>', u'Apples <>'),
        ...             (u'3', u'Pears'),
        ...         ]
        ...     }
        ... )
        >>> print field.checkbox_group('fruit', sub_name='id')
        <input type="checkbox" name="fruit[0].id" value="1" checked="checked" /> Bananas
        <input type="checkbox" name="fruit[1].id" value="2&gt;" /> Apples &lt;&gt;
        <input type="checkbox" name="fruit[2].id" value="3" checked="checked" /> Pears
        >>> print field.checkbox_group('fruit', sub_name='id', align='vert')
        <input type="checkbox" name="fruit[0].id" value="1" checked="checked" /> Bananas<br />
        <input type="checkbox" name="fruit[1].id" value="2&gt;" /> Apples &lt;&gt;<br />
        <input type="checkbox" name="fruit[2].id" value="3" checked="checked" /> Pears<br />
        >>> print field.checkbox_group('fruit', sub_name='id', align='table', cols=2)
        <table border="0" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td><input type="checkbox" name="fruit[0].id" value="1" checked="checked" /> Bananas</td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
              <td><input type="checkbox" name="fruit[1].id" value="2&gt;" /> Apples &lt;&gt;</td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            </tr>
            <tr>
              <td><input type="checkbox" name="fruit[2].id" value="3" checked="checked" /> Pears</td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
              <td></td>
              <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            </tr>
        </table>

        This also works with more deeply nested fields:

        >>> field = Field(
        ...     value={
        ...         u'person[0].fruit[0].id': u'1',
        ...         u'person[0].fruit[1].id': u'3',
        ...     },
        ...     option={
        ...         u'person[*].fruit[*].id': [
        ...             (u'1', u'Bananas'),
        ...             (u'2>', u'Apples <>'),
        ...             (u'3', u'Pears'),
        ...         ]
        ...     }
        ... )
        >>> print field.checkbox_group('person[0].fruit', sub_name='id')
        <input type="checkbox" name="person[0].fruit[0].id" value="1" checked="checked" /> Bananas
        <input type="checkbox" name="person[0].fruit[1].id" value="2&gt;" /> Apples &lt;&gt;
        <input type="checkbox" name="person[0].fruit[2].id" value="3" checked="checked" /> Pears
        """
        if sub_name is None:
            raise Exception('Expected a sub_name argument')
        if name.endswith(']') and sub_name:
            raise Exception('The name should not end with %r when using sub_name'%name[name.rfind('['):])
        # Format the selected values into the correct flattened structure
        if sub_name:
            selected_values = []
            for k, v in self.value.items():
                if k.startswith(name+'[') and k.endswith('].'+sub_name):
                    selected_values.append(v)
        else:
            selected_values = self.value.get(name) or []
        return group(
            name,
            selected_values,
            _get_option(self, None, name, sub_name),
            'checkbox',
            align,
            cols,
            sub_name
        )

def _get_option(form, option, name, sub_name=None):
    if option is None:
        if not sub_name:
            real_options = form.option.get(name, [])
        else:
            # First see if there is an exact match for this key
            real_options = None
            for option in form.option:
                if option == name+'.'+sub_name:
                    real_options = form.option[option]
            # Otherwise treat all the keys as regexes and merge the options
            # of any matching keys
            found = []
            if real_options is None:
                for option in form.option:
                    key = name+'.'+sub_name
                    match = re.match(option.replace('[', '\[').replace(']', '\]'), key)
                    if match is None:
                        if found:
                            raise Exception('The option keys %r and %r both match this checkbox group %r'%(found[0], option, key))
                        else:
                            found.append(option)
            if found:
                real_options = form.option[found[0]]
    else:
        real_options = option
    return real_options or []

#
# Layout Methods
#

def _ensure_flat_and_set(self, name, value):
    if value is None:
        setattr(self, name, {})
    else:
        if not isinstance(value, dict):
            raise Exception('Expected the %s argument to be a dictionary, not %s'%(name, type(value)))
        for k in value:
            if not isinstance(value[k], unicode):
                try:
                    value[k] = unicode(value[k])
                except Exception( e):
                    raise Exception(
                        'Values of the %r dict must always be a unicode '
                        'string, the key %r is %r, type %r and could not '
                        'be automatically converted to unicode because of '
                        'the following error: %s'%(
                            name,
                            k,
                            value[k],
                            type(value[k]),
                            e,
                        )
                    )
        setattr(self, name, value)

class Form(Field):
    def __init__(
        self,
        value=None,
        option=None,
        checked=None,
        error=None,
        label=None,
    ):
        Field.__init__(self, value, option, checked)
        _ensure_flat_and_set(self, 'error', error)
        _ensure_flat_and_set(self, 'label', label)

    #
    # Form Methods
    #

    def start(self, action="", method="post", enctype=None, attributes=None):
        """\
        Open a form tag which submits via the POST method. You must close the
        form yourself.

        ``action``
            The URL the form will submit to. Defaults to ``''`` so that the
            form submits to the current URL

        ``method``
            Can be ``post`` or ``get`` and affects the HTTP method used to
            submit the form.

        ``enctype``
            The encoding type, only usually set if your form contains fields
            for uploading a file.

        ``attributes``
            A dictionary containing other HTML attributes (apart from
            ``action``, ``method`` and ``enctype``)

        Here are some examples:

        >>> from formbuild import Form
        >>> form = Form()
        >>> print form.start("/submit")
        <form action="/submit" method="post">
        >>> print form.start("/submit", method="get")
        <form action="/submit" method="get">


        If your form contains file fields you must use ``method='post`` (the
        default) and also set the ``enctype`` attribute to contain the value
        ``"multipart/form-data"`` otherwise your browser will submit the
        filename instead of the file content. Here's an example:

        >>> print form.start(
        ...     "/submit",
        ...     "post",
        ...     enctype="multipart/form-data",
        ... )
        <form action="/submit" method="post" enctype="multipart/form-data">
        """                            
        attributes = check_attributes(attributes, ['method', 'enctype', 'action'])
        if method.lower() in ['post', 'get']:
            attributes['method'] = method
        if enctype is not None:
            attributes['enctype'] = enctype
        attributes["action"] = action
        return self.builder.html_open('form', False, attributes or {})

    def end(self, hidden_field_names=None):
        """\
        End a form, adding hidden fields for any values with names in the
        ``hidden_field_names`` list.

        >>> form = Form()
        >>> print form.end()
        </form>
        >>> form = Form(value={'firstname': u'James', 'surname': u'Gardner'})
        >>> print form.end(hidden_field_names=['firstname', 'surname'])
        <input type="hidden" name="firstname" value="James" />
        <input type="hidden" name="surname" value="Gardner" />
        </form>
        """
        if hidden_field_names:
            return Markup('\n'.join([
                '<input type="hidden" name="'+field+'" value="'+self.value.get(field, '')+'" />' for field in hidden_field_names
            ])+u'\n</form>')
        else:
            return Markup(u'</form>')

    #
    # Fieldset methods
    #

    def fieldset_start(self, legend=None, name=None):
        """\
        >>> form = Form(error=dict(person=u"This is an error message"))
        >>> print form.fieldset_start(),
        <fieldset>
        >>> print form.fieldset_end(),
        </fieldset>
        >>> print form.fieldset_start(u'People'),
        <fieldset>
        <legend>People</legend>
        >>> print form.fieldset_start(u'People', u'person'),
        <fieldset>
        <legend>People</legend>
        <span class="error">This is an error message</span>
        """
        html = Markup(u'<fieldset>\n')
        if legend is not None:
            html += self.builder.html_open(u'legend', False, dict())+legend+self.builder.html_close(u'legend')
        if name and self.error.get(name) is not None:
            html += Markup('\n<span class="error">')+self.error.get(name)+Markup('</span>')
        return html

    def fieldset_end(self):
        """\
        >>> form = Form()
        >>> print form.fieldset_end(),
        </fieldset>
        """
        return Markup(u'</fieldset>\n')

    def _get_field(self, name, type, args):
        if type in ['checkbox_group', 'radio_group']:
            field_html = getattr(self, type)(
                name,
                **(args or {})
            )
        else:
            field_html = getattr(self, type)(
                name,
                **(args or {})
            )
        return field_html

    def field(
        self,
        name,
        type,
        label='',
        error='',
        required=False,
        field_desc='',
        field_pre='',
        args=None,
        colon=True,
        required_position='before',
    ):
        """\
        Generate a field with a label and any error.
        """
        if required and required_position not in ['before', 'after']:
            raise Exception("The required_position argument can either be 'before' or 'after', not %r"%required_position)
        html = Markup('')
        if args and 'attributes' in args and 'id' in args['attributes']:
            html += self.builder.html_open('label', close=False, attributes={'for': args['attributes']['id']})
        else:
            html += self.builder.html_open('label', close=False)
        if required and required_position=='before':
            html += '*'
        html += label or self.label.get(name, '')
        if required and required_position=='after':
            html += '*'
        if colon:
            html += ':'
        html += self.builder.html_close('label')
        if error or self.error.get(name):
            html += Markup('<span class="error">%s</span>')%(error or self.error.get(name))
        if field_pre:
            html += field_pre + Markup('<br />')
        html += self._get_field(name, type, args)+u'\n'
        if field_desc:
            html += Markup('<br />') + field_desc
        html += Markup('<br />')
        return html

    def action_bar(self, actions):
        """\
        Enter some HTML into the form layout starting at the same level as the
        fields.

        This is useful for generating an action bar containing submit buttons.

        ``actions``
            A ``Markup()`` object representing the HTML for the actions

        >>> form = Form()
        >>> print form.action_bar(
        ...     Markup('\\n'.join([
        ...         form.submit('submit', '< Back'),
        ...         form.submit('submit', 'Forward >')
        ...     ]))
        ... ),
        <input type="submit" name="submit" value="&lt; Back" />
        <input type="submit" name="submit" value="Forward &gt;" />
        
        """
        return Markup(u'').join(actions)+Markup(u'\n')

class TableForm(Form):
    def __init__(
        self,
        value=None,
        option=None,
        checked=None,
        error=None,
        label=None,
        table_class='formbuild'
    ):
        self.table_class = table_class
        Form.__init__(self, value, option, checked, error, label)

    def start_layout(self, table_class=None):
        """\
        Start a layout without adding the form tag

        >>> form=TableForm()
        >>> print form.start_layout()
        <table>
        >>> print form.start_layout(table_class='form')
        <table class="form">
        """
        if table_class is None:
            return Markup(u'<table>')
        else:
            return Markup(u'<table class="%s">')%(table_class)

    def end_layout(self):
        """\
        End a layout without adding the end form tag

        >>> form = TableForm()
        >>> print form.end_layout()
        </table>
        """
        return Markup(u'</table>')

    def start_with_layout(
        self,
        action='',
        method="post",
        enctype=None,
        table_class=None,
        attributes=None
    ):
        """\
        Start a form the way you would with ``start_form()`` but include the
        HTML necessary for the use of the ``fields()`` helper.

        >>> form=TableForm()
        >>> print form.start_with_layout('/action', method='post')
        <form action="/action" method="post"><table class="formbuild">
        >>> print form.start_with_layout('/action', method='post', table_class='form')
        <form action="/action" method="post"><table class="form">
        """
        attributes = check_attributes(attributes, ['method', 'enctype', 'action'])
        if method.lower() in ['post', 'get']:
            attributes['method'] = method
        if enctype is not None:
            attributes['enctype'] = enctype
        attributes["action"] = action
        html = self.builder.html_open('form', False, attributes or {})
        html += self.start_layout(table_class or self.table_class)
        return html

    def end_with_layout(self, hidden_field_names=None):
        """\
        End a form started with ``start_with_layout()``

        >>> form = TableForm()
        >>> print form.end_with_layout()
        </table></form>
        """
        html = ''
        html += '</table>'
        if hidden_field_names:
            html += '\n'.join([
                '<input type="hidden" name="'+field+'" value="'+self.value.get(field, '')+'" />' for field in hidden_field_names
            ])+u'\n</form>'
        else:
            html += u'</form>'
        # XXX Really bad, not guaranteed safe
        return Markup(html)

    def action_bar(self, escaped_html):
        """\
        Enter some HTML into the form layout starting at the same level as the
        fields.

        This is useful for generating an action bar containing submit buttons.

        ``escaped_html``
            An HTML string, properly escaped, containing all the fields to
            appear in the action bar

        >>> form = TableForm()
        >>> print form.action_bar(
        ...     '\\n    '.join([
        ...         form.submit('submit', '< Back'),
        ...         form.submit('submit', 'Forward >')
        ...     ])
        ... )
        <tr>
          <td></td>
          <td colspan="2">
            <input type="submit" name="submit" value="&lt; Back" />
            <input type="submit" name="submit" value="Forward &gt;" />
          </td>
        </tr>
        """
        if isinstance(escaped_html, (list, tuple)):
            escaped_html = '\n'.join(escaped_html)
        # XXX This is really bad, not really guaranteed escaped
        return Markup(u'<tr>\n  <td></td>\n  <td colspan="2">\n    %s\n  </td>\n</tr>'%(
            escaped_html,
        ))

    def row(self, escaped_html):
        """\
        Enter some HTML into the form layout as a new row.

        This is useful for form sections. For example:

        >>> form = TableForm()
        >>> print form.row('<h2>Extra Fields</h2>')
        <tr><td colspan="3"><h2>Extra Fields</h2></td></tr>
        """
        return '<tr><td colspan="3">'+escaped_html+'</td></tr>'

    def field(
        self,
        name,
        type,
        label='',
        required=False,
        label_desc='',
        field_desc='',
        help='',
        field_pre='',
        attributes=None,
        args=None,
        side=True,
        colon=True,
        required_position='before',
    ):
        """\
        Format a field with a label.

        ``label``
            The label for the field

        ``field``
            The HTML representing the field, wrapped in ``literal()``

        ``required``
             Can be ``True`` or ``False`` depending on whether the label
             should be formatted as required or not. By default required
             fields have an asterix.

        ``label_desc``
            Any text to appear underneath the label, level with ``field_desc``

        ``field_desc``
            Any text to appear underneath the field

        ``help``
            Any HTML or JavaScript to appear imediately to the right of the
            field which could be used to implement a help system on the form

        ``field_pre``
            Any HTML to appear immediately above the field.

        ``side``
            Whether the label goes at the side of the field or above it.
            Defaults to ``True``, putting the label at the side.

        TIP: For future compatibility, always specify arguments explicitly
        and do not rely on their order in the function definition.

        Here are some examples:

        >>> form = TableForm(value=dict(test=u''))
        >>> print form.start_with_layout()
        <form action="" method="post"><table class="formbuild">
        >>> print form.field('test', 'text', 'email >', required=True)
        <tr class="field">
          <td class="label" valign="top" height="10">
            <span class="required">*</span><label for="test">email &gt;:</label>
          </td>
          <td class="field" valign="top">
            <input type="text" name="test" value="" />
          </td>
          <td rowspan="2" valign="top"></td>
        </tr>
        >>> print form.field(
        ...     'test',
        ...     'text',
        ...     label='email >',
        ...     label_desc='including the @ sign',
        ...     field_desc='Please type your email carefully',
        ...     help = 'No help available for this field',
        ...     required=True,
        ... )
        ...
        <tr class="field">
          <td class="label" valign="top" height="10">
            <span class="required">*</span><label for="test">email &gt;:</label>
          </td>
          <td class="field" valign="top">
            <input type="text" name="test" value="" />
          </td>
          <td rowspan="2" valign="top">No help available for this field
            </td>
        </tr>
        <tr class="description">
          <td class="label_desc" valign="top">
            <span class="small">including the @ sign</span>
          </td>
          <td class="field_desc" valign="top">
            <span class="small">Please type your email carefully</span>
          </td>
        </tr>
        >>> print form.end_with_layout()
        </table></form>

        An appropriate stylesheet to use to style forms generated with field() when
        the table class is specified as "formbuild" would be::

            table.formbuild span.error-message, table.formbuild div.error, table.formbuild span.required {
                font-weight: bold;
                color: #f00;
            }
            table.formbuild span.small {
                font-size: 85%;
            }
            table.formbuild form {
                margin-top: 20px;
            }
            table.formbuild form table td {
                padding-bottom: 3px;
            }

        """
        field_html = self._get_field(name, type, args)
        error = self.error.get(name)
        error_html = error and u'<div class="error">'+escape(error)+'</div>\n' or u''
        if side == True:
            html = """\
<tr class="field">
  <td class="label" valign="top" height="10">
    %(required_html_before)s<label for="%(label_for)s">%(label_html)s%(colon)s</label>%(required_html_after)s
  </td>
  <td class="field" valign="top">
    %(field_pre_html)s%(error_html)s%(field_html)s
  </td>
  <td rowspan="2" valign="top">%(help_html)s</td>
</tr>"""     %dict(
                required_html_after = required_position == 'after' and (required and u'<span class="required">*</span>' \
                   or u'<span style="visibility: hidden">*</span>') or '',
                required_html_before = required_position == 'before' and (required and u'<span class="required">*</span>' \
                   or u'<span style="visibility: hidden">*</span>') or '',
                label_for = name,
                label_html = escape(label),
                error_html = error_html,
                field_html = field_html,
                help_html = help and escape(help)+'\n    ' or '',
                field_pre_html = field_pre and escape(field_pre) or '',
                colon = colon and ":" or "",
            )
            if label_desc or field_desc:
                html += """
<tr class="description">
  <td class="label_desc" valign="top">
    <span class="small">%(label_desc_html)s</span>
  </td>
  <td class="field_desc" valign="top">
    <span class="small">%(field_desc_html)s</span>
  </td>
</tr>"""         %dict(
                    label_desc_html = label_desc,
                    field_desc_html = field_desc,
                )
        else:
            html = """\
<tr><td></td>
  <td valign="top">
     <table border="0">
        <tr>
          <td><label for="%(label_for)s">%(label_html)s%(colon)s</label></td><td>%(required_html)s</td><td><span class="small label_desc">%(label_desc_html)s</span></td>
        </tr>
     </table>
  </td>
  <td valign="top" rowspan="3">%(help_html)s</td>
</tr>
<tr><td></td>
  <td valign="top">%(field_pre_html)s%(error_html)s%(field_html)s</td>
</tr>
<tr><td></td>
  <td class="small field_desc" valign="top">%(field_desc_html)s</td>
</tr>"""%   dict(
                label_for = name,
                label_html = escape(label),
                help_html = help and escape(help)+'\n    ' or '',
                required_html = required and u'<span class="required">*</span>' \
                   or u'<span style="visibility: hidden">*</span>',
                error_html = error_html,
                field_html = field_html,
                field_pre_html = field_pre and escape(field_pre) or '',
                label_desc_html = label_desc,
                field_desc_html = field_desc,
                colon = colon and ":" or "",
            )
        # XXX This is completely wrong, we haven't tested it
        return Markup(html)

    #def start_fieldset(self, legend=None, name=None):
    #    """\
    #    >>> form = Form(error=dict(person="This is an error"))
    #    >>> print form.start_fieldset()
    #    <fieldset>
    #    >>> print form.end_fieldset()
    #    </fieldset>
    #    >>> print form.start_fieldset(u'People')
    #    <fieldset>
    #    <legend>People</legend>
    #    >>> print form.start_fieldset(u'People', 'person')
    #    <fieldset>
    #    <legend>People</legend>
    #    <p class="error">This is an error message</p>
    #    """
    #    html = u'<fieldset>'
    #    if legend is not None:
    #        html += '\n'+self.builder.html_open(u'legend', False, dict())+legend+self.builder.html_close(u'legend')
    #    if name and self.error.get(name) is not None:
    #        html += '\n<p class="error">'+self.error.get(name)+'</p>'
    #    return html

    #def end_fieldset(self, name):
    #    """\
    #    >>> form = Form()
    #    >>> print form.end_fieldset()
    #    </fieldset>
    #    """
    #    return u'</fieldset>'

