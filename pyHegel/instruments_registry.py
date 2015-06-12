# -*- coding: utf-8 -*-

########################## Copyrights and license ############################
#                                                                            #
# Copyright 2011-2015  Christian Lupien <christian.lupien@usherbrooke.ca>    #
#                                                                            #
# This file is part of pyHegel.  http://github.com/lupien/pyHegel            #
#                                                                            #
# pyHegel is free software: you can redistribute it and/or modify it under   #
# the terms of the GNU Lesser General Public License as published by the     #
# Free Software Foundation, either version 3 of the License, or (at your     #
# option) any later version.                                                 #
#                                                                            #
# pyHegel is distributed in the hope that it will be useful, but WITHOUT     #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or      #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public        #
# License for more details.                                                  #
#                                                                            #
# You should have received a copy of the GNU Lesser General Public License   #
# along with pyHegel.  If not, see <http://www.gnu.org/licenses/>.           #
#                                                                            #
##############################################################################

from __future__ import absolute_import

from collections import defaultdict
from . import instruments

_instruments_ids = {}
_instruments_ids_rev = defaultdict(list)
_instruments_usb = {}
_instruments_add = {}

def clean_instruments():
    for name in _instruments_add:
        delattr(instruments, name)
    _instruments_add.clear()

def _add_to_instruments(some_object, name=None):
    if name is None:
        # this works for classes and functions
        name = some_object.__name__
    if _instruments_add.has_key(name):
        if _instruments_add[name] is some_object:
            # already installed
            return name
        raise RuntimeError('There is already a different entry "%s"=%s, so unable to install %s'%(
            name, _instruments_add[name], some_object))
    # not installed yet
    if hasattr(instruments, name):
        raise RuntimeError('There is already an attribute "%s" within the instruments package'%(name))
    setattr(instruments, name, some_object)
    _instruments_add[name] = some_object
    return name


def find_instr(manuf=None, product=None, firmware_version=None):
    """
    look for a matching instrument to the manuf, product, firmware_version
    specification. It tries a complete match first and then matches with
    instruments not specifying firmware_version, then not specifying product.
    It returns the instrument or raises KeyError.
    manuf could be the 3 element tuple
    """
    if isinstance(manuf, tuple):
        key = manuf
    else:
        key = (manuf, product, firmware_version)
    keybase = key
    try:
        return _instruments_ids[key]
    except KeyError:
        pass
    # try a simpler key
    key = key[:2]+(None,)
    try:
        return _instruments_ids[key]
    except KeyError:
        pass
    # try the simplest key
    key = (key[0], None, None)
    try:
        return _instruments_ids[key]
    except KeyError:
        raise KeyError(keybase)


def find_usb(vendor_id, product_id=None):
    """ vendor_id can be the vendor_id or a tuple of vendor_id, product_id
        The search looks for an exact match followed by a match for
        instruments only specifying vendor_id
    """
    if isinstance(vendor_id, tuple):
        key = vendor_id
    else:
        key = (vendor_id, product_id)
    keybase = key
    try:
        return _instruments_usb[key]
    except KeyError:
        pass
    # try a simpler key
    key = (key[0], None)
    try:
        return _instruments_usb[key]
    except KeyError:
        raise KeyError(keybase)


def check_instr_id(instr, idn_manuf, product=None, firmware_version=None):
    """
    idn is either the 3 element tuple (manuf, product, firmware version)
    or the value of manuf
    Returns True if there is a match found. Otherwise False.
    Note that the check works for overrides.
    """
    if not isinstance(idn_manuf, tuple):
        idn_manuf = (idn_manuf, product, firmware_version)
    return idn_manuf in _instruments_ids_rev[instr]


# The following functions are to be used as decorators
def register_instrument(manuf=None, product=None, firmware_version=None, usb_vendor_product=None, quiet=False, skip_add=False):
    """
    If you don't specify any of the options, the instrument will only be added to the instruments
    module. It will not be searchable.
    usb_vendor_product needs to be a tuple (vendor_id, product_id), where both ids are 16 bit integers.
    product_id could be None to match all devices with vendor_id (should be rarelly used).
    Similarly you should specify manuf and product together to match them agains the returned
    values from SCPI *idn?. You can also specify firmware_version (the 4th member of idn) to only
    match instruments with that particular firmware.

    You can use multiple register_instrument decorator on an instruments.

    quiet prevents the warning registration override
    skip_add prevents the adding of the instrument into the instruments module namespace.
    """
    def _internal_reg(instr_class):
        if not skip_add:
            name = _add_to_instruments(instr_class)
        if manuf is not None:
            if ',' in manuf:
                raise ValueError("manuf can't contain ',' for %s"%instr_class)
            if product is not None and ',' in product:
                raise ValueError("product can't contain ',' for %s"%instr_class)
            key = (manuf, product, firmware_version)
            if not quiet and _instruments_ids.has_key(key):
                print ' Warning: Registering %s with %s to override %s'%(
                        key, instr_class, _instruments_ids[key])
            _instruments_ids[key] = instr_class
            _instruments_ids_rev[instr_class].append(key)
        if usb_vendor_product is not None:
            vid, pid = usb_vendor_product
            if vid<0 or vid>0xffff:
                raise ValueError('Out of range vendor id for %s'%instr_class)
            if pid is not None and (pid<0 or pid>0xffff):
                raise ValueError('Out of range product id for %s'%instr_class)
            key = usb_vendor_product
            if not quiet and _instruments_usb.has_key(key):
                print ' Warning: Registering usb %s with %s to override %s'%(
                        key, instr_class, _instruments_usb[key])
            _instruments_usb[key] = instr_class
        return instr_class
    return _internal_reg


def add_to_instruments(name=None):
    """ Use this decorator function to insert the object in the instruments
        module namespace. This is not needed if you already used
        register_instrument.
        Note that if you don't specify name, it will use the class or function name.
        For an object that does not possess a __name__ attribute, you need to
        specify name.
        Remember that even if name is not given, this is a function so use it like
         @add_to_instruments()
         some_object....
    """
    def _internal_add(some_object):
        _add_to_instruments(some_object, name)
        return some_object
    return _internal_add

# TODO: deal with usb database
