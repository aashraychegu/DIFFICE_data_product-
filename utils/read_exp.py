import collections
from typing import Union, List
import os
# pyrefly: ignore [missing-import]
from pathlib import Path
# pyrefly: ignore [missing-import]
import numpy as np

def read_exp(filename: Union[str,Path]) -> List:
    """
    Read contours from an exp file.

    This function reads contour data from a file in *.exp format. The function can handle
    files containing multiple contours. Each contour is returned as a dictionary
    containing coordinate data, metadata, and geometric properties.

    Parameters
    ----------
    filename : str
        Path to the input exp file

    Returns
    -------
    contours : list of dict
        List of contour data read from the file. Each contour dictionary contains:
        - 'x' : np.ndarray
            X coordinates of the contour points
        - 'y' : np.ndarray  
            Y coordinates of the contour points
        - 'name' : str
            Name of the contour from the file
        - 'density' : float
            Density value for the contour
        - 'nods' : int
            Number of nodes/points in the contour
        - 'icon' : str, optional
            Icon value from the file, if present
        - 'closed' : bool
            Whether the contour is closed (first and last points are identical)

    Raises
    ------
    IOError
        If the input file does not exist

    Notes
    -----
    The function expects exp files with specific formatting including contour headers,
    point counts, density values, and coordinate data. The function handles variations
    in header spacing (e.g., '# Points Count Value' vs '# Points Count  Value').
    Invalid formatting may cause parsing errors.

    Examples
    --------
    >>> contours = read_exp('input.exp')
    >>> print(f"Read {len(contours)} contours")
    >>> for contour in contours:
    ...     print(f"Contour '{contour['name']}' has {contour['nods']} points")
    """

    # Error checks
    if not os.path.exists(filename):
        raise IOError(f"pyissm.tools.exp.read_exp: File {filename} does not exist.")
    
    # Initialise contours
    contours = []
    contour = None
    
    # Open the file for reading and loop over lines
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip blank lines
            if not line:
                continue
            
            # If Name line, start a new contour
            if line.startswith('## Name:'):
                
                ## Save previous contour if it exists
                if contour is not None:
                    contours.append(contour)
                
                ## Create empty contour
                contour = collections.OrderedDict({
                    'name': line.split('## Name:')[1].strip(),
                    'x': [],
                    'y': [],
                })

            # If Icon line, extract information
            elif line.startswith('## Icon:'):
                contour['icon'] = line.split('## Icon:')[1].strip()

            # If Points Count Value line, read point count and density
            ## NOTE: Some files have '# Points Count Value' and some have '# Points Count  Value'. This handles both.
            elif line.startswith('# Points Count'):
                ## Get next line for point count and density
                nods_line = next(f).strip()

                ## Split the line and extract values
                nods_parts = nods_line.split()
                contour['nods'] = int(nods_parts[0])
                contour['density'] = float(nods_parts[1])

            # If X pos Y pos line, read coordinate data
            elif line.startswith('# X pos Y pos'):
                ## Create empty contour coordinate arrays
                contour['x'] = np.empty(contour['nods'])
                contour['y'] = np.empty(contour['nods'])
                
                ## Read the next 'nods' lines for coordinates
                for i in range(contour['nods']):
                    coord_line = next(f).strip()
                    x_str, y_str = coord_line.split()
                    contour['x'][i] = (float(x_str))
                    contour['y'][i] = (float(y_str))

                ## Check if contour is closed
                contour['closed'] = (
                    contour['nods'] > 1
                    and (contour['x'][-1] == contour['x'][0]) 
                    and (contour['y'][-1] == contour['y'][0])
                )                

        # Append the final contour to the list
        if contour is not None:
            contours.append(contour)

    return contours