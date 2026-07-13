from pathlib import Path
import subprocess


USER_GROUPS_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "entrypoint"
    / "user_groups.sh"
)


def _run_setup_user_and_groups(identity_exists: bool) -> list[str]:
    result = subprocess.run(
        [
            "bash",
            "-c",
            r'''
. "$1"
IDENTITY_EXISTS="$2"
source() { :; }
box_echo() { :; }
getent() {
    if [ "$IDENTITY_EXISTS" != "true" ]; then
        return 2
    fi
    case "$1" in
        group) printf 'appuser:x:1000:\n' ;;
        passwd) printf 'appuser:x:1000:1000::/home/appuser:/bin/sh\n' ;;
        *) return 1 ;;
    esac
}
groupadd() { printf 'groupadd %s\n' "$*"; }
useradd() { printf 'useradd %s\n' "$*"; }
usermod() { printf '%s\n' "$*"; }
setup_user_and_groups
''',
            "bash",
            str(USER_GROUPS_SCRIPT),
            str(identity_exists).lower(),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.splitlines()


def test_existing_user_keeps_primary_group_in_supplementary_memberships() -> None:
    assert _run_setup_user_and_groups(identity_exists=True) == [
        "-aG appuser appuser"
    ]


def test_new_user_keeps_primary_group_in_supplementary_memberships() -> None:
    assert _run_setup_user_and_groups(identity_exists=False) == [
        "groupadd -g 1000 appuser",
        "useradd -u 1000 -g 1000 -m appuser",
        "-aG appuser appuser",
    ]
