# diag077 local build rejection

No remote launch or GPU reservation occurred. The local smoke rejected the
generated notebook because the extracted nested cache-hash function retained its
source indentation when inserted into cell 0. The immutable failed snapshot is
retained. Successor diag078 dedents the identical function before insertion.
