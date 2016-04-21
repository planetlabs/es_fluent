.. :changelog:

History
-------

0.0.4 (2016-04-21)
---------------------

* Fixing `is_empty` so it works properly on nested boolean filters - an
  `AndFilter` with an empty `AndFilter` inside of it is empty, overall.
