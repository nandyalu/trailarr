# Plex Connection

Adding a Plex connection is optional, but unlocks some powerful features:

- **Automatic media linking** — Trailarr matches your Radarr/Sonarr media to the corresponding items in your Plex libraries, keeping everything in sync.
- **Plex trailer detection** — Trailarr can check whether Plex already has a trailer for a media item and skip downloading if one already exists (configurable per profile).
- **Plex notifications** — After a trailer is downloaded, Trailarr can trigger a Plex library scan so the trailer appears in Plex immediately (configurable per profile).

!!! note ""
    A Plex connection works alongside your existing Radarr/Sonarr connections — it does not replace them. You still need at least one Radarr or Sonarr connection to use Trailarr.

---

## Adding a Plex Connection

### 1. Start the Setup

- Navigate to `Settings > Connections`.
- Click the `Add New` button.
- Set **Arr Type** to `Plex`.

### 2. Sign in with Plex (OAuth)

- Click the **Sign in with Plex** button. A popup window will open and take you to Plex's authorization page.
- Sign in with your Plex account and grant Trailarr access.
- Once authorized, the popup will close automatically and Trailarr will receive your Plex token.

!!! tip ""
    Make sure your browser does not block popups for the Trailarr page, otherwise the OAuth window will not open.

### 3. Select Your Plex Server

- After authorization, Trailarr will fetch the list of Plex servers available on your account.
- Select the server you want to connect to from the dropdown.
- Trailarr will automatically fill in the **Server URL** and **Machine Identifier**.

### 4. Save the Connection

- Give your connection a friendly name (e.g., `Plex`).
- Click **Submit** to save.

!!! note "No Path Mappings Required"
    Unlike Radarr and Sonarr connections, Plex does not need path mappings. Trailarr communicates with Plex directly via its API and does not need access to your Plex media files.

---

## What Happens Next

Once the Plex connection is saved, Trailarr will begin linking your existing media items to their corresponding entries in Plex during the next connection sync. You can watch this happen in real time on the [Events](../../user-guide/events/index.md) page — look for `Plex Linked` events.

For each successfully linked item, Trailarr will know whether Plex already has a trailer, which can then be used by your [Trailer Profiles](../../user-guide/settings/profiles/index.md) to skip unnecessary downloads.

!!! tip "Configure Plex behaviour per profile"
    Head to `Settings > Profiles`, edit a profile, and look for the **Plex** section to enable trailer skip logic and Plex notifications. See the [Plex profile settings](../../user-guide/settings/profiles/settings/plex.md) reference for details.
