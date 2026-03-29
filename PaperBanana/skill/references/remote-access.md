# Remote Access

Local machine:

```bash
python run.py --host 127.0.0.1 --port 8501
```

Open:

```text
http://127.0.0.1:8501
```

Remote server over SSH:

Server:

```bash
python run.py --host 127.0.0.1 --port 8501
```

Local machine:

```bash
ssh -L 8501:127.0.0.1:8501 <user>@<server>
```

Then open:

```text
http://127.0.0.1:8501
```

Direct port exposure:

```bash
python run.py --host 0.0.0.0 --port 8501
```

Then open:

```text
http://<server-ip>:8501
```

Use direct exposure only when network access is intentionally configured.
