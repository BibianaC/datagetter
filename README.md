# 360Giving Data Getter

Install dependencies:

```
python3 -m virtualenv -p $(which python3) .ve
source .ve/bin/activate
pip install -r requirements.txt
```

Run:

```
mkdir -p data/original data/json
python get.py
```