Interpret packed binary data using named attributes
===================================================
The structer package provides metaclasses which allow concise specification of code to unpack binary data.

The first application of this code, build_ids.py,
extracts build ID values from a Linux core file which includes a file note that lists the mappings,
and which includes the first block of each shared library in the link map, and the executable.

The cpio module handles CPIO files with magic number 070701 or 070702.
The rpm module uses the cpio module, and the top level rpm.py script extracts build ID values from the specified RPM.
