'''
Extension of the pandas dataframe to be more flexible, especially with filtering
rows/columns and concatenating data.
'''

##############################################################################
#%% Dataframe
##############################################################################

import numbers # For numeric type
import numpy as np
import pandas as pd
from . import sc_utils as scu
from . import sc_math as scm
from . import sc_odict as sco


__all__ = ['dataframe']

class dataframe(pd.DataFrame):
    '''
    An extension of the pandas :class:`DataFrame <pandas.DataFrame>` with additional convenience methods for
    accessing rows and columns and performing other operations, such as adding rows.
    
    Args:
        data (dict/array/dataframe): the data to use; passed to :class:`pd.DataFrame() <pandas.DataFrame>`
        index (array): the index to use; passed to :class:`pd.DataFrame() <pandas.DataFrame>`
        columns (list): column labels (if a dict is supplied, the value sets the dtype)
        dtype (type): a dtype for the whole datafrmae; passed to :class:`pd.DataFrame() <pandas.DataFrame>`
        dtypes (list/dict): alternatively, list of data types to set each column to
        nrows (int): the number of arrows to preallocate (default 0)
        kwargs (dict): if provided, treat these as data columns
    
    *Hint*: Run the example below line by line to get a sense of how the dataframe
    changes.

    **Examples**::

        df = sc.dataframe(cols=['x','y'], data=[[1238,2],[384,5],[666,7]]) # Create data frame
        df['x'] # Print out a column
        df[0] # Print out a row
        df['x',0] # Print out an element
        df[0,:] = [123,6]; print(df) # Set values for a whole row
        df['y'] = [8,5,0]; print(df) # Set values for a whole column
        df['z'] = [14,14,14]; print(df) # Add new column
        df.rmcol('z'); print(df) # Remove a column
        df.addcol('z', [14,14,14]); print(df) # Alternate way to add new column
        df.poprow(1); print(df) # Remove a row
        df.append([555,2,14]); print(df) # Append a new row
        df.insertrow(1,[556,2,14]); print(df) # Insert a new row
        df.sort(); print(df) # Sort by the first column
        df.sort('y'); print(df) # Sort by the second column
        df.findrow(123) # Return the row starting with value 123
        df.rmrow(); print(df) # Remove last row
        df.rmrow(555); print(df) # Remove the row starting with element '555'
        
        # Direct setting of data
        df = sc.dataframe(a=[1,2,3], b=[4,5,6])

    The dataframe can be used for both numeric and non-numeric data.

    | *New in version 2.0.0:* subclass pandas DataFrame
    | *New in version 3.0.0:* "dtypes" argument; handling of item setting
    '''

    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=None, 
                 dtypes=None, nrows=None, **kwargs):
        
        # Handle inputs
        if 'cols' in kwargs:
            columns = kwargs.pop('cols')
        if nrows and data is None:
            ncols = len(columns)
            data = np.zeros((nrows, ncols))
        
        # Handle columns and dtypes
        if isinstance(columns, dict):
            if dtypes is not None:
                errormsg = 'You can supply dtypes as a separate argument or as part of a columns dict, but not both'
                raise ValueError(errormsg)
            dtypes = columns # Already in the right format
            columns = list(columns.keys())
        if isinstance(data, dict):
            if columns is not None:
                colset = sorted(set(columns))
                dataset = sorted(set(data.keys()))
                if colset != dataset:
                    errormsg = f'Incompatible column names provided:\nColumns: {colset}\n   Data: {dataset}'
                    raise ValueError(errormsg)
        
        # Handle data
        if kwargs:
            if data is None:
                data = kwargs
            elif isinstance(data, dict):
                data.update(kwargs)
            else:
                errormsg = f'Cannot combine non-dict data {type(data)} with keyword arguments "{scu.strjoin(kwargs.keys())}"'
                raise TypeError(errormsg)

        # Create the dataframe
        super().__init__(data=data, index=index, columns=columns, dtype=dtype, copy=copy)
        
        # Optionally set dtypes
        if dtypes is not None:
            self.set_dtypes(dtypes)
        
        return


    @property
    def cols(self):
        ''' Get columns as a list '''
        return self.columns.tolist()


    def set_dtypes(self, dtypes):
        '''
        Set dtypes in-place (see :meth:`df.astype() <pandas.DataFrame.astype>` for the user-facing version)
        
        *New in version 3.0.0.*
        '''
        if not isinstance(dtypes, dict):
            dtypes = {col:dtype for col,dtype in zip(self.columns, dtypes)}
        for col,dtype in dtypes.items(): # NB: "self.astype(dtypes, copy=False)" does not modify in place
            self[col] = self[col].astype(dtype)
        return


    def col_index(self, col=None, *args, die=True):
        '''
        Get the index of the column named ``col``.
        
        Similar to ``df.columns.get_loc(col)``, and opposite of :meth:`df.col_name <dataframe.col_name>`.
        
        Args:
            col (str/list): the column(s) to get the index of (return 0 if None)
            args (list): additional column(s) to get the index of
            die (bool): whether to raise an exception if the column could not be found (else, return None)
        
        **Examples**::
            
            df = sc.dataframe(dict(a=[1,2,3], b=[4,5,6], c=[7,8,9]))
            df.col_index('b') # Returns 1
            df.col_index(1) # Returns 1
            df.col_index('a', 'c') # Returns [0, 2]
            
        *New in version 3.0.0:* renamed from "_sanitizecols"; multiple arguments
        '''
        arglist = scu.mergelists(col, list(args), keepnone=True)
        outputlist = []
        cols = self.cols
        for col in arglist:
            if col is None:
                output = 0 # If not supplied, assume first column is intended
            elif col in cols:
                output = cols.index(col) # Convert to index
            elif scu.isnumber(col):
                try:
                    cols[col]
                except IndexError as E: # pragma: no cover
                    errormsg = f'Column "{col}" is not a valid index; there are {len(cols)} columns'
                    raise IndexError(errormsg) from E
                output = col
            else: # pragma: no cover
                errormsg = f'Unrecognized column/column type "{col}" {type(col)}'
                if die:
                    raise TypeError(errormsg)
                else:
                    print(errormsg)
                    output = None
            outputlist.append(output)
        if len(outputlist) == 1:
            outputlist = outputlist[0]
        return outputlist
    
    
    def col_name(self, col=None, *args, die=True):
        '''
        Get the name of the column(s) with index ``col``.
        
        Similar to ``df.columns[col]``, and opposite of :meth:`df.col_index <dataframe.col_index>`.
        
        **Note**: This method always looks for named columns first. If ``col`` is 
        name of a column, it will return ``col`` rather than ``columns[col]``. See
        example below for more information.
        
        Args:
            col (int/list): the column(s) to get the index of (return 0 if None)
            args (list): additional column(s) to get the index of
            die (bool): whether to raise an exception if the column could not be found (else, return None)
        
        **Examples**::
            
            df = sc.dataframe(dict(a=[1,2,3], b=[4,5,6], c=[7,8,9]))
            df.col_name(1) # Returns 'b'
            df.col_name('b') # Returns 'b'
            df.col_name(0, 2) # Returns ['a', 'c']
        
        *New in version 3.0.0.*
        '''
        arglist = scu.mergelists(col, list(args), keepnone=True)
        outputlist = []
        cols = self.cols
        for col in arglist:
            if col is None:
                col = 0 # If not supplied, assume first column is intended
            elif col in cols:
                output = col # It's already a column
            elif scu.isnumber(col):
                try:
                    output = cols[col]
                except Exception as E: # pragma: no cover
                    errormsg = f'Column "{col}" is not a valid index'
                    raise IndexError(errormsg) from E
            else: # pragma: no cover
                errormsg = f'Unrecognized column/column type "{col}" {type(col)}'
                if die:
                    raise TypeError(errormsg)
                else:
                    print(errormsg)
                    output = None
            outputlist.append(output)
        if len(outputlist) == 1:
            outputlist = outputlist[0]
        return outputlist


    def get(self, key):
        ''' Alias to pandas __getitem__ method; rarely used '''
        return super().__getitem__(key)
    
    
    def set(self, key, value=None):
        ''' Alias to pandas __setitem__ method; rarely used '''
        return super().__setitem__(key, value)


    def __getitem__(self, key=None, die=True, cast=True):
        ''' Simple method for returning; see self.flexget() for a version based on col and row '''
        try: # Default to the pandas version
            output = super().__getitem__(key)
        except: # ...but handle a wider variety of keys
            try:
                output = super().iloc[key]
            except:
                if scu.isstring(key): # e.g. df['a'] -- usually handled by pandas # pragma: no cover
                    rowindex = slice(None)
                    try:
                        colindex = self.cols.index(key)
                    except ValueError:
                        errormsg = f'Key "{key}" is not a valid column; choices are: {scu.strjoin(self.cols)}'
                        raise scu.KeyNotFoundError(errormsg)
                elif isinstance(key, (numbers.Number, list, np.ndarray, slice)): # e.g. df[0], df[[0,2]], df[:4]
                    rowindex = key
                    colindex = slice(None)
                elif isinstance(key, tuple):
                    rowindex = key[0]
                    colindex = key[1]
                    if scu.isstring(rowindex) and not scu.isstring(colindex): # Swap order if one's a string and the other isn't
                        rowindex, colindex = colindex, rowindex
                    if scu.isstring(colindex): # e.g. df['a',0]
                        colindex = self.cols.index(colindex)
                else: # pragma: no cover
                    errormsg = f'Unrecognized dataframe key of {type(key)}: must be str, numeric, or tuple'
                    if die:
                        raise scu.KeyNotFoundError(errormsg)
                    else:
                        print(errormsg)
                        output = None
                output = self.iloc[rowindex,colindex]

        return output


    def __setitem__(self, key, value=None):
        try:
            # Use regular pandas for everything except keys that look like (0,'a'), ('a',0), (0,0), or (0,:)
            if isinstance(key, tuple) and (key not in self.columns) and (len(key) == 2) and all([isinstance(k, (int, str, Ellipsis)) for k in key]):
                raise NotImplementedError # Break out of the loop
            super().__setitem__(key, value)
        except Exception as E1:
            cols = self.cols
            try:
                rowindex = key[0]
                colindex = key[1]
                if rowindex in cols and colindex not in cols: # Swap order if one's a string and the other isn't
                    rowindex, colindex = colindex, rowindex
                if colindex in cols: # e.g. df['a',0]
                    colindex = cols.index(colindex)
                self.iloc[rowindex, colindex] = value
            except Exception as E2: # pragma: no cover
                if isinstance(E1, NotImplementedError): # We tried to raise it, so only care about the second one
                    mainerr = E2
                    errstr = f'\n{E2}'
                else: # An actual pandas error, raise both
                    mainerr = E1
                    errstr = f'\n{E1}\n{E2}'
                exc = type(mainerr)
                errormsg = f'Could not understand key {key}:{errstr}'
                raise exc(errormsg) from mainerr
        return


    def flexget(self, cols=None, rows=None, asarray=False, cast=True, default=None):
        '''
        More complicated way of getting data from a dataframe. While getting directly
        by key usually returns the array data directly, this usually returns another
        dataframe.

        Args:
            cols (str/list): the column(s) to get
            rows (int/list): the row(s) to get
            asarray (bool): whether to return an array (otherwise, return a dataframe)
            cast (bool): attempt to cast to an all-numeric array
            default (any): the value to return if the column(s)/row(s) can't be found

        **Example**::

            df = sc.dataframe(cols=['x','y','z'],data=[[1238,2,-1],[384,5,-2],[666,7,-3]]) # Create data frame
            df.flexget(cols=['x','z'], rows=[0,2])
        '''
        if cols is None: # pragma: no cover
            colindices = Ellipsis
        else:
            colindices = []
            for col in scu.tolist(cols):
                colindices.append(self.col_index(col))
        if rows is None: # pragma: no cover
            rowindices = Ellipsis
        else:
            rowindices = rows

        output = self.iloc[rowindices,colindices] # Split up so can handle non-consecutive entries in either
        if output.size == 1:
            output = np.array(output).flatten()[0] # If it's a single element, return the value rather than the array
        elif asarray:
            output = np.array(output)
        else:
            output = self._constructor(data=output, columns=np.array(self.cols)[colindices].tolist())

        return output


    def __eq__(self, other):
        '''
        Allow for equality checks: same type, size, columns, and values
        
        *New in version 3.0.0.*
        '''
        
        # Check type
        if not isinstance(other, self.__class__):
            return False
        
        # Check shape
        if self.values.shape != other.values.shape:
            return False

        # Check columns
        if not np.all(self.columns == other.columns):
            return False
        
        # Check values
        if not np.all(self.values == other.values):
            return False
        
        # Passed all checks
        return True


    def disp(self, nrows=None, ncols=None, width=999, precision=4, options=None, **kwargs):
        '''
        Flexible display of a dataframe, showing all rows/columns by default.
        
        Args:
            nrows (int): maximum number of rows to show (default: all)
            ncols (int): maximum number of columns to show (default: all)
            width (int): maximum screen width (default: 999)
            precision (int): number of decimal places to show (default: 4)
            options (dict): an optional dictionary of additional options, passed to :class:`pd.option_context() <pandas.option_context>`
            kwargs (dict): also passed to :class:`pd.option_context() <pandas.option_context>`, with 'display.' preprended if needed
        
        **Examples**::
            
            df = sc.dataframe(data=np.random.rand(100,10))
            df.disp()
            df.disp(precision=1, ncols=5, colheader_justify='left')
        
        *New in version 2.0.1.*
        '''
        kwdict = {}
        for k,v in kwargs.items():
            key = k
            if k in dir(pd.options.display):
                key = f'display.{k}'
            kwdict[key] = v
        opts = scu.mergedicts({
            'display.max_rows': nrows,
            'display.max_columns': ncols,
            'display.width': width,
            'display.precision': precision,
            },
            options,
            kwdict,
        )
        optslist = [item for pair in opts.items() for item in pair] # Convert from dict to list
        with pd.option_context(*optslist):
            print(self)
        return


    def replacedata(self, newdata=None, newdf=None, reset_index=True, inplace=True):
        '''
        Replace data in the dataframe with other data; usually not used directly
        by the user, but used as part of e.g. :meth:`df.concat() <dataframe.concat>`.

        Args:
            newdata (array): replace the dataframe's data with these data
            newdf (dataframe): substitute the current dataframe with this one
            reset_index (bool): update the index
            inplace (bool): whether to modify in-place
        
        *New in version 3.0.0:* improved dtype handling
        '''
        if newdf is None: # pragma: no cover
            newdf = self._constructor(data=newdata, columns=self.columns)
        if reset_index:
            newdf.reset_index(drop=True, inplace=True)
        if inplace:
            self._update_inplace(newdf, verify_is_copy=False)
            return self
        else:
            return newdf


    def appendrow(self, row, reset_index=True, inplace=True):
        '''
        Add row(s) to the end of the dataframe. 
        
        See also :meth:`df.concat() <dataframe.concat>` and :meth:`df.insertrow() <dataframe.insertrow>`. Similar to the pandas operation
        ``df.iloc[-1] = ...``, but faster and provides additional type checking.

        Args:
            value (array): the row(s) to append
            reset_index (bool): update the index
            inplace (bool): whether to modify in-place
        
        Note: "appendrow" and "concat" are equivalent, except appendrow() defaults
        to modifying in-place and "concat" defaults to returning a new dataframe.
        
        Warning: modifying dataframes in-place is quite inefficient. For highest
        performance, construct the data in large chunks and then add to the dataframe
        all at once, rather than adding row by row.
        
        **Example**::
            
            import sciris as sc
            import numpy as np

            df = sc.dataframe(dict(
                a = ['foo','bar'], 
                b = [1,2], 
                c = np.random.rand(2)
            ))
            df.appendrow(['cat', 3, 0.3])           # Append a list
            df.appendrow(dict(a='dog', b=4, c=0.7)) # Append a dict
            
        *New in version 3.0.0:* renamed "value" to "row"; improved performance
        '''
        return self.concat(row, reset_index=reset_index, inplace=inplace)
    
    
    def append(self, row, reset_index=True, inplace=True):
        '''
        Alias to :meth:`appendrow() <dataframe.appendrow>`.
        
        **Note**: `pd.DataFrame.append` was deprecated in pandas version 2.0; see
        https://github.com/pandas-dev/pandas/issues/35407 for details. Since this
        method is implemented using :func:`pd.concat() <pandas.concat>`, it does
        not suffer from the performance problems that ``append`` did.
        
        *New in version 3.0.0.*
        '''
        return self.concat(row, reset_index=reset_index, inplace=inplace)


    def insertrow(self, index=0, value=None, reset_index=True, inplace=True, **kwargs):
        '''
        Insert row(s) at the specified location. See also :meth:`df.concat() <dataframe.concat>`
        and :meth:`df.appendrow() <dataframe.appendrow>`.

        Args:
            index (int): index at which to insert new row(s)
            value (array): the row(s) to insert
            reset_index (bool): update the index
            inplace (bool): whether to modify in-place
            kwargs (dict): passed to `:meth:`df.concat() <dataframe.concat>`
        
        Warning: modifying dataframes in-place is quite inefficient. For highest
        performance, construct the data in large chunks and then add to the dataframe
        all at once, rather than adding row by row.
        
        **Example**::
            
            import sciris as sc
            import numpy as np

            df = sc.dataframe(dict(
                a = ['foo','cat'], 
                b = [1,3], 
                c = np.random.rand(2)
            ))
            df.insertrow(1, ['bar', 2, 0.2])           # Insert a list
            df.insertrow(0, dict(a='rat', b=0, c=0.7)) # Insert a dict
        
        *New in version 3.0.0:* renamed "row" to "index"
        '''
        before = self.iloc[:index,:]
        after  = self.iloc[index:,:]
        newdf = self.cat(before, value, after, **kwargs)
        return self.replacedata(newdf=newdf, reset_index=reset_index, inplace=inplace)


    def _sanitize_df(self, arg, columns=None, **kwargs):
        ''' Helper function to sanitize input into the correct format for constructing a new dataframe '''
        if isinstance(arg, pd.DataFrame):
            df = arg
        else:
            if isinstance(arg, dict):
                columns = list(arg.keys())
                arg = list(arg.values())
            argarray = arg if isinstance(arg, np.ndarray) else np.array(arg) # Solely for checking the shape
            if argarray.shape == (self.ncols,): # If it's a single row with the right number of columns, make 2D
                arg = [arg]
            df = self._constructor(data=arg, columns=columns, **kwargs)
        return df


    def concat(self, data, *args, columns=None, reset_index=True, inplace=False, dfargs=None, **kwargs):
        '''
        Concatenate additional data onto the current dataframe. 
        
        Similar to :meth:`df.appendrow() <dataframe.appendrow>` and :meth:`df.insertrow() <dataframe.insertrow>`;
        see also :meth:`df.cat() <dataframe.cat>` for the equivalent class method.
        
        Args:
            data (dataframe/array): the data to concatenate
            *args (dataframe/array): additional data to concatenate
            columns (list): if supplied, columns to go with the data
            reset_index (bool): update the index
            inplace (bool): whether to append in place
            dfargs (dict): arguments passed to construct each dataframe
            **kwargs (dict): passed to :func:`pd.concat() <pandas.concat>`
        
        | *New in version 2.0.2:* "inplace" defaults to False
        | *New in version 3.0.0:* improved type handling
        '''
        dfargs = scu.mergedicts(dfargs)
        dfs = [self]
        if columns is None:
            columns = self.columns
        for arg in [data] + list(args):
            df = self._sanitize_df(arg, columns=columns, **dfargs)
            dfs.append(df)
        newdf = self._constructor(pd.concat(dfs, **kwargs), **dfargs)
        return self.replacedata(newdf=newdf, reset_index=reset_index, inplace=inplace)


    @classmethod
    def cat(cls, data, *args, dfargs=None, **kwargs):
        '''
        Convenience method for concatenating multiple dataframes. See :meth:`df.concat() <dataframe.concat>`
        for the equivalent instance method.
        
        Args:
            data (dataframe/array): the dataframe/data to use as the basis of the new dataframe
            args (list): additional dataframes (or object that can be converted to dataframes) to concatenate
            dfargs (dict): arguments passed to construct each dataframe
            kwargs (dict): passed to :func:`df.concat() <dataframe.concat>`
        
        **Example**::
            
            arr1 = np.random.rand(6,3)
            df2 = pd.DataFrame(np.random.rand(4,3))
            df3 = sc.dataframe.cat(arr1, df2)
        
        *New in version 2.0.2.*
        '''
        dfargs = scu.mergedicts(dfargs)
        df = cls(data, **dfargs)
        if len(args):
            df = df.concat(*args, dfargs=dfargs, **kwargs)
        return df
            

    def merge(self, *args, reset_index=True, inplace=False, **kwargs):
        '''
        Alias to :func:`pd.merge <pandas.merge>`, except merge in place.
        
        Args:        
            reset_index (bool): update the index
            inplace (bool): whether to append in place
            **kwargs (dict): passed to :func:`pd.concat() <pandas.concat>`
            
        *New in version 3.0.0.*
        
        **Example**::
            
            df = sc.dataframe(dict(x=[1,2,3], y=[4,5,6]))
            df2 = sc.dataframe(dict(x=[1,2,3], z=[9,8,7]))
            df.merge(df2, on='x', inplace=True)
        '''
        newdf = self._constructor(pd.merge(self, *args, **kwargs))
        return self.replacedata(newdf=newdf, reset_index=reset_index, inplace=inplace)


    @property
    def ncols(self):
        ''' Get the number of columns in the dataframe '''
        return len(self.columns)


    @property
    def nrows(self):
        ''' Get the number of rows in the dataframe '''
        return len(self)


    def addcol(self, key=None, value=None):
        ''' Add a new column to the data frame -- for consistency only '''
        return self.__setitem__(key, value)


    def popcols(self, col=None, *args, die=True):
        '''
        Remove a column or columns from the data frame.
        
        Alias to :meth:`pop() <pandas.DataFrame.pop>`, except allowing multiple
        columns to be popped.
        
        Args:
            col (str/list): the column(s) to be popped
            args (list): additional columns to pop
            die (bool): whether to raise an exception if a column is not found
        
        **Example**::
            
            df = sc.dataframe(cols=['a','b','c','d'], data=np.random.rand(3,4))
            df.popcols('a','c')
        '''
        cols = scu.mergelists(col, list(args), keepnone=True)
        for col in cols:
            if col not in self.columns: # pragma: no cover
                errormsg = f'sc.dataframe(): cannot remove column {col}: columns are:\n{scu.newlinejoin(self.cols)}'
                if die: raise Exception(errormsg)
                else:   print(errormsg)
            else:
                self.pop(col)
        return self


    def findind(self, value=None, col=None, closest=False, die=True):
        '''
        Find the row index for a given value and column.
        
        See :meth:`df.findrow() <dataframe.findrow>` for the equivalent to return the row itself
        rather than the index of the row. See :meth:`df.col_index() <dataframe.col_index>` for the column
        equivalent.
        
        
        Args:
            value (any): the value to look for (default: return last row index)
            col (str): the column to look in (default: first)
            closest (bool): if true, return the closest match if an exact match is not found
            die (bool): whether to raise an exception if the value is not found (otherwise, return None)
        
        **Example**::
            
            df = sc.dataframe(data=[[2016,0.3],[2017,0.5]], columns=['year','val'])
            df.findind(2016) # returns 0
            df.findind(0.5, 'val') # returns 1
            df.findind(2013) # returns None, or exception if die is True
            df.findind(2013, closest=True) # returns 0
        
        *New in version 3.0.0:* renamed from "_rowindex"
        '''
        col = self.col_index(col)
        coldata = self.iloc[:,col].values # Get data for this column
        if value is None: # pragma: no cover
            return len(coldata)-1 # If not supplied, pick the last element
        if closest: # pragma: no cover
            index = np.argmin(abs(coldata-value)) # Find the closest match to the key
        else:
            try:
                index = coldata.tolist().index(value) # Try to find duplicates
            except: # pragma: no cover
                if die:
                    errormsg = f'Item {value} not found; choices are: {coldata}'
                    raise IndexError(errormsg)
                else:
                    return
        return index
    

    def _diffinds(self, inds=None):
        ''' For a given set of indices, get the inverse, in set-speak '''
        if inds is None: inds = []
        all_inds = np.arange(self.nrows)
        these_inds = all_inds[inds]
        diff_set = np.setdiff1d(all_inds, these_inds)
        return diff_set


    def poprow(self, row=-1, returnval=True):
        '''
        Remove a row from the data frame.
        
        Alias to :meth:`drop <pandas.DataFrame.drop>`, except drop by position
        rather than label, and modify in-place. To pop multiple rows, see
        meth:`df.poprows() <dataframe.poprows>`.
        
        Args:
            row (int): index of the row to pop
            returnval (bool): whether to return the row that was popped
        
        To pop a column, see :meth:`df.pop() <pandas.DataFrame.pop>`.
        
        *New in version 3.0.0:* "key" argument renamed "row"
        '''
        if isinstance(row, int):
            rowindex = row
            indexkey = self.index[row]
        else: # It's a string (most likely): find the corresponding index
            rowindex = self.index.get_indexer(row)
            indexkey = row
        if returnval:
            thisrow = self.iloc[rowindex,:]
        self.drop(indexkey, inplace=True)
        if returnval:
            return thisrow
        else:
            return self


    def poprows(self, inds=-1, value=None, col=None, reset_index=True, inplace=True, **kwargs):
        '''
        Remove multiple rows by index or value
        
        To pop a single row, see meth:`df.poprow() <dataframe.poprow>`.
        
        Args:
            inds (list): the rows to remove
            values (list): alternatively, search for these values to remove; see :meth:`df.findinds <dataframe.findinds>` for details
            col (str): if removing by value, use this column to find the values
            reset_index (bool): update the index
            inplace (bool): whether to modify in-place
            kwargs (dict): passed to :meth:`df.findinds <dataframe.findinds>`
        
        **Examples**::
            
            df = sc.dataframe(np.random.rand(10,3))
            df.poprows([3,4,5])
            
            df = sc.dataframe(dict(x=[0,1,2,3,4], y=[2,3,2,7,8]))
            df.poprows(value=2, col='y')
        '''
        if value is not None:
            inds = self.findinds(value=value, col=col, **kwargs)
        keep_set = self._diffinds(inds)
        keep_data = self.iloc[keep_set,:]
        newdf = self._constructor(data=keep_data, cols=self.cols)
        return self.replacedata(newdf=newdf, reset_index=reset_index, inplace=inplace)


    def replacecol(self, col=None, old=None, new=None):
        ''' Replace all of one value in a column with a new value '''
        col = self.col_index(col)
        coldata = self.iloc[:,col] # Get data for this column
        inds = scm.findinds(arr=coldata, val=old)
        self.iloc[inds,col] = new
        return self


    def to_odict(self, row=None):
        '''
        Convert dataframe to a dict of columns, optionally specifying certain rows.

        Args:
            row (int/list): the rows to include
        '''
        if row is None:
            row = slice(None)
        data = self.iloc[row,:].values
        datadict = {col:data[:,c] for c,col in enumerate(self.cols)}
        output = sco.odict(datadict)
        return output


    def findrow(self, value=None, col=None, default=None, closest=False, asdict=False, die=False):
        '''
        Return a row by searching for a matching value.
        
        See :meth:`df.findind() <dataframe.findind>` for the equivalent to return the index of the row
        rather than the row itself, and :meth:`df.findinds() <dataframe.findinds>`
        to find multiple row indices.

        Args:
            value (any): the value to look for
            col (str): the column to look for this value in
            default (any): the value to return if key is not found (overrides die)
            closest (bool): whether or not to return the closest row (overrides default and die)
            asdict (bool): whether to return results as dict rather than list
            die (bool): whether to raise an exception if the value is not found

        **Examples**::

            df = sc.dataframe(cols=['year','val'],data=[[2016,0.3],[2017,0.5], [2018, 0.3]])
            df.findrow(2016) # returns array([2016, 0.3], dtype=object)
            df.findrow(2013) # returns None, or exception if die is True
            df.findrow(2013, closest=True) # returns array([2016, 0.3], dtype=object)
            df.findrow(2016, asdict=True) # returns {'year':2016, 'val':0.3}
        '''
        index = self.findind(value=value, col=col, die=(die and default is None), closest=closest)
        if index is not None:
            thisrow = self.iloc[index,:].values
            if asdict:
                thisrow = self.to_odict(thisrow)
        else:
            thisrow = default # If not found, return as default
        return thisrow


    def findinds(self, value=None, col=None, **kwargs):
        '''
        Return the indices of all rows matching the given key in a given column.
        
        Args:
            value (any): the value to look for
            col (str): the column to look in
            kwargs (dict): passed to :func:`sc.findinds() <sc_math.findinds>`
        
        **Example**::
            
            df = sc.dataframe(cols=['year','val'],data=[[2016,0.3],[2017,0.5], [2018, 0.3]])
            df.findinds(0.3, 'val') # Returns array([0,2])
        '''
        col = self.col_index(col)
        coldata = self.iloc[:,col].values # Get data for this column
        inds = scm.findinds(arr=coldata, val=value, **kwargs)
        return inds


    def _filterrows(self, inds=None, value=None, col=None, keep=True, verbose=False, reset_index=True, inplace=False):
        ''' Filter rows and either keep the ones matching, or discard them '''
        if value is not None:
            inds = self.findinds(value=value, col=col)
        if keep: inds = self._diffinds(inds)
        if verbose: print(f'Dataframe filtering: {len(inds)} rows removed based on key="{inds}", column="{col}"')
        output = self.poprows(inds=inds, reset_index=reset_index, inplace=inplace)
        return output


    def filterin(self, inds=None, value=None, col=None, verbose=False, reset_index=True, inplace=False):
        '''
        Keep only rows matching a criterion; see also :meth:`df.filterout() <dataframe.filterout>`
        '''
        return self._filterrows(inds=inds, value=value, col=col, keep=True, verbose=verbose, reset_index=reset_index, inplace=inplace)


    def filterout(self, inds=None, value=None, col=None, verbose=False, reset_index=True, inplace=False):
        '''
        Remove rows matching a criterion (in place); see also :meth:`df.filterin() <dataframe.filterin>`
        '''
        return self._filterrows(inds=inds, value=value, col=col, keep=False, verbose=verbose, reset_index=reset_index, inplace=inplace)


    def filtercols(self, cols=None, *args, keep=True, die=True, reset_index=True, inplace=False):
        '''
        Filter columns keeping only those specified -- note, by default, do not perform in place
        
        Args:
            cols (str/list): the columns to keep (or remove if keep=False)
            args (list): additional columns
            keep (bool): whether to keep the named columns (else, remove them)
            die (bool): whether to raise an exception if a column is not found
            reset_index (bool): update the index
            inplace (bool): whether to modify in-place
        
        **Examples**::
            
            df = sc.dataframe(cols=['a','b','c','d'], data=np.random.rand(3,4))
            df2 = df.filtercols('a','b') # Keeps columns 'a' and 'b'
            df3 = df.filtercols('a','c', keep=False) # Keeps columns 'b' and 'd'
        '''
        cols = scu.mergelists(cols, list(args), keepnone=True)
        order = []
        notfound = []
        for col in cols:
            try:
                order.append(self.cols.index(col))
            except ValueError: # pragma: no cover
                cols.remove(col)
                notfound.append(col)
        if len(notfound): # pragma: no cover
            errormsg = 'sc.dataframe(): could not find the following column(s): %s\nChoices are: %s' % (notfound, self.cols)
            if die: raise Exception(errormsg)
            else:   print(errormsg)
        if not keep: # pragma: no cover
            order = np.setdiff1d(np.arange(len(self.cols)), order)
            cols = [self.cols[o] for o in order]
        ordered_data = self.iloc[:,order] # Resort and filter the data
        newdf = self._constructor(cols=cols, data=ordered_data)
        return self.replacedata(newdf=newdf, reset_index=reset_index, inplace=inplace)


    def sortrows(self, by=None, reverse=False, returninds=False, reset_index=True, inplace=True, **kwargs):
        '''
        Sort the dataframe rows in place by the specified column(s).
        
        Similar to :meth:`df.sort_values() <pandas.DataFrame.sort_values>`, except defaults to sorting in place, and
        optionally returns the indices used for sorting (like :func:`np.argsort() <numpy.argsort>`).
        
        Args:
            col (str or int): column to sort by (default, first column)
            reverse (bool): whether to reverse the sort order (i.e., ascending=False)
            returninds (bool): whether to return the indices used to sort instead of the dataframe
            reset_index (bool): update the index
            inplace (bool): whether to modify the dataframe in-place
            kwargs (dict): passed to :meth:`df.sort_values() <pandas.DataFrame.sort_values>`
        
        *New in version 3.0.0:* "inplace" argument; "col" argument renamed "by"
        '''
        by = kwargs.pop('col', by) # Handle deprecation
        ascending = kwargs.pop('ascending', not(reverse))
        if by is None:
            by = 0 # Sort by first column by default
        if isinstance(by, int):
            by = self.columns[by]
        if returninds:
            sortorder = np.argsort(self[by].values, kind='mergesort') # To preserve order
        df = self.sort_values(by=by, ascending=ascending, inplace=inplace, **kwargs)
        if reset_index:
            self.reset_index(drop=True, inplace=True)
        if returninds:
            return sortorder
        else:
            if inplace:
                return self
            else:
                return df
    
    
    def sort(self, by=None, reverse=False, returninds=False, inplace=True, **kwargs):
        '''
        Alias to :meth:`sortrows() <dataframe.sortrows>`.
        
        *New in version 3.0.0.*
        '''
        return self.sortrows(by=by, reverse=reverse, returninds=returninds, inplace=True, **kwargs)


    def sortcols(self, sortorder=None, reverse=False, inplace=True):
        '''
        Like sortrows(), but change column order (usually in place) instead.
        
        Args:
            sortorder (list): the list of indices to resort the columns by (if none, then alphabetical)
            reverse (bool): whether to reverse the order
            inplace (bool): whether to modify the dataframe in-place
        
        *New in version 3.0.0:* Ensure dtypes are preserved; "inplace" argument; "returninds" argument removed
        '''
        if sortorder is None:
            sortorder = np.argsort(self.cols, kind='mergesort')
            if reverse:
                sortorder = sortorder[::-1]
        newcols = list(np.array(self.cols)[sortorder])
        newdf = dataframe({k:self[k] for k in newcols})
        return self.replacedata(newdf=newdf, inplace=inplace)


    def to_pandas(self, **kwargs):
        ''' Convert to a plain pandas dataframe '''
        return pd.DataFrame(self)

    @classmethod
    def read_csv(cls, *args, **kwargs):
        ''' Alias to :func:`pd.read_csv <pandas.read_csv`, returning a Sciris dataframe '''
        return cls(pd.read_csv(*args, **kwargs))

    @classmethod
    def read_excel(cls, *args, **kwargs):
        ''' Alias to :func:`pd.read_excel <pandas.read_excel`, returning a Sciris dataframe '''
        return cls(pd.read_excel(*args, **kwargs))

    @property
    def _constructor(self):
        ''' Overload pandas method to ensure correct type; replaces :class:`pd.DataFrame() <pandas.DataFrame>` '''
        return self.__class__ # To allow subclassing