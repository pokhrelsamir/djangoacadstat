# Project Structure

Use this guide during presentation to quickly explain where the main files are.

## Runtime folders

| Folder / file | Purpose |
| --- | --- |
| `manage.py` | Django command entry point |
| `academicsys/` | Project settings, main URLs, WSGI |
| `core/` | Main academic app: models, views, forms, URLs, templates |
| `api/` | API entry point |
| `static/` | Project-wide CSS, JavaScript, and images |
| `media/` | Uploaded files such as student images and materials |
| `requirements.txt` | Python dependencies |
| `vercel.json` and `build_files.sh` | Deployment configuration |

## Presentation and support folders

| Folder | Purpose |
| --- | --- |
| `docs/commands/` | Django, PostgreSQL, and Git command notes |
| `docs/feature-guides/` | Feature-specific notes |
| `docs/specifications/` | Feature specs and presentation notes |
| `docs/reports/` | Project reports and summaries |
| `docs/install-logs/` | Old dependency/install logs |
| `scripts/setup/` | Setup scripts |
| `scripts/debug/checks/` | Debug/check helper scripts |
| `scripts/debug/traces/` | Trace and analysis helper scripts |
| `scripts/debug/repairs/` | One-off repair helper scripts |
| `scripts/debug/tests/` | Local test/run helper scripts |
| `scripts/patches/` | Patch scripts |
| `data/backups/` | Database/export backups |
| `samples/bulk_marks_upload/` | Sample upload templates |
| `logs/` | Local server logs |

## Do not move for demo

Keep these in place because Django or deployment expects them here:

- `.env`
- `manage.py`
- `academicsys/`
- `core/`
- `static/`
- `media/`
- `requirements.txt`
- `vercel.json`
- `build_files.sh`
