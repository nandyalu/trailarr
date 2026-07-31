# Backup & Restore

Trailarr automatically backs up its database on **every startup**, right before running
any database migrations. You never need to do anything for backups to happen — this
page explains where they live and how to use one to recover or roll back to a previous
version.

## Where backups live

Backups are stored inside your config folder (`APP_DATA_DIR`), next to the database:

```text
/config/                     # your mapped config folder (Docker default)
├── trailarr.db              # the live database
└── backups/
    ├── trailarr_20260705081530.db
    ├── trailarr_20260628102201.db
    └── ...                  # most recent 30 backups are kept automatically
```

Each file is a complete copy of the database, named
`trailarr_YYYYMMDDHHMMSS.db` with the time the app started. Trailarr keeps the **30
most recent** backups and deletes older ones automatically.

> 💡 Since a backup is taken on every startup, restarting Trailarr right before an
> upgrade guarantees you have a fresh pre-upgrade backup.

## No downgrade below v0.11.0

{{ version_badge("add", "0.11.0") }}

The `v0.11.0` upgrade removes old database fields. Because of this, you cannot downgrade to an earlier version after it runs. To go back, restore the pre-upgrade backup (see below) and start the older version.

Also since `v0.11.0`, Trailarr runs a `VACUUM` on the database after migrations apply. The database file can become smaller after an upgrade. This is normal: `VACUUM` returns free space to the filesystem. It is not data loss or corruption.

## Restore a backup

Use this when the database is damaged, or something went wrong after an upgrade.

1. **Stop Trailarr** (`docker stop trailarr`, or stop the service for direct installs).
2. In your config folder, keep a copy of the current database just in case:

    ```bash
    mv /path/to/config/trailarr.db /path/to/config/trailarr.db.broken
    ```

3. Copy the backup you want over the live database:

    ```bash
    cp /path/to/config/backups/trailarr_YYYYMMDDHHMMSS.db /path/to/config/trailarr.db
    ```

4. **Start Trailarr again.**

That's it. If the app version is the same or newer than the one that wrote the backup,
any needed database migrations run automatically on startup — restoring an older
backup into a newer version is always safe.

## Roll back to a previous version

If a new release misbehaves for you, roll back the app **and** the database together:

1. **Stop Trailarr.**
2. **Restore the backup taken before the upgrade** (see above — pick the newest backup
   from *before* the day you upgraded).
3. **Pin the previous image version** instead of `:latest`. In your compose file:

    ```yaml
    services:
      trailarr:
        image: nandyalu/trailarr:0.9.8   # the version you're rolling back to
    ```

    Then `docker compose up -d`. For direct installs, reinstall the previous release.

4. After Trailarr is up, verify your library looks right, and please
   [open an issue](https://github.com/nandyalu/trailarr/issues) describing what went
   wrong with the newer version — rollbacks are a bug report we want to hear about.

> ⚠️ **Always restore a matching (or older) backup when downgrading.** A database that
> was migrated by a newer version is **not** compatible with an older app version —
> starting an old version against a new database can fail in confusing ways. The
> pre-upgrade backup is exactly the right file for a rollback.

## Notes

- Backups cover the **database only** (media records, downloads, profiles, settings
  stored in the DB). Your `.env` settings file, downloaded trailer files, and images
  live outside the database and are untouched by upgrades or restores.
- Want an extra safety net? Include the whole config folder in your normal backup
  tooling (it's small) — that covers `.env` and the backups folder itself.
