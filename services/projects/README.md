# projects

## Run examples

**Note!** Variable `AUTH_REQUIRED` must be `false` (in `.env`) 
before running script `demo_ws.py`.

Folder *examples/* contains simple examples of client for communication with 
tracking servers.


0) **Remove** old folder *workspace/* if it exists


1) run fastapi application:

```bash
docker-compose up
```

2) setup virtual environment (in new terminal window):

```bash
cd examples/

virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run demo notebook

```bash
cd notebooks/
jupyter-notebook demo.ipynb
```
    
## Generate demo workspace

run script:

```bash
python demo_ws.py
```
    
  
## Troubleshooting

If database schema is updated, but you local tracking database is old, you'll show error 
message (with code 500) on any request:

```
{
  "message": "Bad (obsolete) table project schema, missing columns: {'path', 'id', 'created_at'}. Remove content of workspace/ and rerun application", 
  "status": "fail"
}
```

Just remove old database version in folder `workspace` or better remove all folder content.