Interpret packed binary data using named attributes
===================================================
The structer package provides metaclasses which allow concise specification of code to unpack binary data.

The first application of this code, build_ids.py,
extracts build ID values from a Linux core file which includes a file note that lists the mappings,
and which includes the first block of each shared library in the link map, and the executable.
