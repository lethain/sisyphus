# Installation

* start redis...
* create a whoosh directory and a reference to it in ``settings.py``

    import os
    whoosh_index = whoosh.index.open_dir(settings.WHOOSH_INDEXDIR)


# Importing Data

    python blog/manage.py shell
    import sisyphus.scripts.import_from_lifeflow