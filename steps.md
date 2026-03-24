for migrating data from sqlite to postgres follow this steps:

1. you need a copy of the full sqlite database
2. create a fixture from the sqlite db (from branch main)

```code
python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes -o fixture.json
```

copy the file fixture.json to this folder (use git worktree to make your life easier)

3. use ```make build``` to build the container

4. use ```make loaddata``` to load the fixtures into the postgres db

5. you can now start the server with ```make up```

if you don't have make install you can see the commands on the Makefile file in this repo
