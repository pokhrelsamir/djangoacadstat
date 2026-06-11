# Data

Runtime data files that are not part of the application source code.

## Contents

| Folder      | Purpose                                      |
|-------------|----------------------------------------------|
| `backups/`  | JSON database backups created by `backup_db` |

Backups are generated via:

```bash
python manage.py backup_db
```
