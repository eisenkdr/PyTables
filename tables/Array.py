########################################################################
#
#       License: BSD
#       Created: October 10, 2002
#       Author:  Francesc Alted - falted@openlc.org
#
#       $Source: /home/ivan/_/programari/pytables/svn/cvs/pytables/pytables/tables/Array.py,v $
#       $Id: Array.py,v 1.7 2003/01/29 16:52:09 falted Exp $
#
########################################################################

"""Here is defined the Array class.

See Array class docstring for more info.

Classes:

    Array

Functions:


Misc variables:

    __version__


"""

__version__ = "$Revision: 1.7 $"

import types
from Leaf import Leaf
import hdf5Extension
import Numeric
import chararray
import numarray

class Array(Leaf, hdf5Extension.Array):
    """Represent a Numeric Array in HDF5 file.

    It provides methods to create new arrays or open existing ones, as
    well as methods to write/read data and metadata to/from array
    objects over the HDF5 file.

    All Numeric typecodes are supported except "F" and "D" which
    corresponds to complex datatypes.

    Methods:

        read()
        flush()  # This can be moved to Leaf
        close()  # This can be moved to Leaf

    Instance variables:

        name -- the node name
        title -- the node title  # This can be moved to Leaf
        shape -- tuple with the array shape (in Numeric sense)
        typecode -- the typecode for the array

    """
    
    def __init__(self, NumericObject = None, title = "", atomic = 1):
        """Create the instance Array.

        Keyword arguments:

        NumericObject -- Numeric array to be saved. If None, the
            metadata for the array will be taken from disk.

        "title" -- Sets a TITLE attribute on the HDF5 array entity.
        "atomic" -- If an HDF5 datatype is to used.

        """
        # Check if we have to create a new object or read their contents
        # from disk
        if NumericObject is not None:
            self._v_new = 1
            self.object = NumericObject
            self.title = title
            self.atomic = atomic
        else:
            self._v_new = 0
            
    def create(self):
        """Save a fresh array (i.e., not present on HDF5 file)."""
        # Call the createArray superclass method to create the table
        # on disk

        obversion = "1.0"    # default version for ARRAY objects
        arr = self.object
        # Check for Numeric objects
        if isinstance(arr, numarray.NumArray):
            flavor = "NUMARRAY"
            naarr = arr
        elif type(arr) == type(Numeric.array(1)):
            flavor = "NUMERIC"
            if arr.typecode() == "c":
                shape = list(arr.shape)
                itemsize = shape.pop()
                naarr = chararray.array(buffer(arr),
                                        itemsize=itemsize,
                                        shape=shape)
            else:
                # This the fastest way to convert from Numeric to numarray
                # because no data copy is involved
                naarr = numarray.array(buffer(arr),
                                       type=arr.typecode(),
                                       shape=arr.shape)

        elif (isinstance(arr, types.TupleType) or
              isinstance(arr, types.ListType)):
            # Test if can convert to numarray object
            try:
                naarr = numarray.array(arr)
            # If not, test with a chararray
            except TypeError:
                try:
                    naarr = chararray.array(arr)
                # If still doesn't, issues an error
                except:
                    raise ValueError, \
"""The object '%s' can't be converted to a numerical or character array.
  Sorry, but this object is not supported.""" % (arr)
            if isinstance(arr, types.TupleType):
                flavor = "TUPLE"
            else:
                flavor = "LIST"
        else:
            raise ValueError, \
"""The object '%s' is not in the list of supported objects (numarray,
  chararray,homogeneous list or homogeneous tuple).
  Sorry, but this object is not supported.""" % (arr)

        print "Array to saved:", naarr
        self.typecode = self.createArray(naarr, self.title,
                                         flavor, obversion, self.atomic)
        # Get some important attributes
        self.shape = naarr.shape

    def open(self):
        """Get the metadata info for an array in file."""
        (self.typecode, self.shape, self.typesize) = self.openArray()
        #self.title = self.getArrayTitle()
        self.title = self._v_parent._f_getDsetAttr(self._v_name, "TITLE")
        # NUMERIC, NUMARRAY, TUPLE, LIST or other flavor 
        self.flavor = self._v_parent._f_getDsetAttr(self._v_name, "FLAVOR")
        #print "Flavor -->", self.flavor
        
    # Accessor for the readArray method in superclass
    def read(self):
        """Read the array from disk and return it as Numeric."""
        print "Typecode ==>", repr(self.typecode)
        if repr(self.typecode) == "CharType":
            arr = chararray.array(None, itemsize=self.typesize,
                                  shape=self.shape)
        else:
            arr = numarray.array(buffer=None,
                                 type=self.typecode,
                                 shape=self.shape)
        # Do the actual data read
        self.readArray(arr._data)
        
        # Convert to Numeric, tuple or list if needed
        print "read arr -->", arr
        if self.flavor == "NUMERIC":
            # This works for both numeric and chararrays
            # arr=Numeric.array(arr, typecode=arr.typecode())
            # The next is 10 times faster
            arr=Numeric.array(arr.tolist(), typecode=arr.typecode())
        elif self.flavor == "TUPLE":
            arr = tuple(arr.tolist())
        elif self.flavor == "LIST":
            arr = arr.tolist()
        
        return arr
        
    def flush(self):
        """Save whatever remaining data in buffer."""
        # This is a do nothing method because, at the moment the Array
        # class don't support buffers
    
    def close(self):
        """Flush the array buffers and close this object on file."""
        self.flush()