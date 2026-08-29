# How the frontend is arranged

Angular 22, standalone components, Signals, zoneless change detection. There are no NgModules.

## Folders

| Folder | What is in it |
|---|---|
| `auth/` | The login page and the guard that protects the routes. |
| `events/` | The Events page. |
| `logs/` | The Logs page. |
| `media/` | The media list and the media details page. This is the main feature area, and the largest folder. |
| `models/` | TypeScript interfaces for the data the API returns. |
| `nav/` | The top bar, the side navigation and the mobile bottom bar. |
| `notifications/` | The notification channels page. |
| `services/` | One service per API area, plus the websocket service. Components call these; they do not call `fetch` themselves. |
| `settings/` | Every settings page, including Connections, Profiles and Health. |
| `shared/` | Parts that more than one feature uses. See below. |
| `tasks/` | The Tasks page. |

## What goes in `shared/`

A feature folder owns what only it uses. `shared/` is for the parts that two or more features use.

- `shared/<component>/` — a component, with its own folder. `load-indicator/`, `help-link-icon/` and `path-select-dialog/` are the pattern to copy.
- `shared/pipes/` — every pipe.
- `shared/directives/` — every directive.

Pipes and directives lived in `helpers/` until Phase 7. They moved here so that one folder answers "where is the shared code", instead of two.

## Rules

1. **A component is standalone.** List what it needs in its own `imports`.
2. **State is a Signal.** Change detection is zoneless, so a plain field does not trigger a render.
3. **A component talks to a service, never to the API.** The services in `services/` wrap the generated client.
4. **Styles use the Material Design 3 tokens.** Never write a color or a shadow directly. `CLAUDE.md` lists the tokens.
5. **A shared component keeps its files together** in one folder: `.ts`, `.html`, `.scss` and `.spec.ts`.

## Tests

`npm run test` runs Vitest against `*.spec.ts`. A test sits beside the file it covers.

`npm run test` and `npm run build` do not prove that a change works. Build the frontend, start the real app with `python3 scripts/launch.py`, and drive it. The root `CLAUDE.md` explains why: the dev server proxy is a different code path from the way the built files are served in production.
