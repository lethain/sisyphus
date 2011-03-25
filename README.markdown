# Installation

    pip install whoosh python-markdown redis

* start redis...
* create a whoosh directory and a reference to it in ``settings.py``

    import os
    whoosh_index = whoosh.index.open_dir(settings.WHOOSH_INDEXDIR)


# Importing Data

    python blog/manage.py shell
    import sisyphus.scripts.import_from_lifeflow

# Deployment

Send changes to the remote host:

    git checkout dev
    git merge master
    git push origin dev

Actually roll the changes out on the remote host:

    ssh your-server
    cd ~/git/sisyphus
    git checkout master
    git merge dev
    sudo apache2ctl
