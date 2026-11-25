import argparse
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Hyprland displays.")
    commands = parser.add_subparsers(dest="command", required=True)
    reposition = commands.add_parser(
        "reposition", help="Set a display position and save the layout."
    )
    reposition.add_argument("connector")
    reposition.add_argument("x", type=int)
    reposition.add_argument("y", type=int)
    args = parser.parse_args()
    subprocess.run(
        ["hyprdisplay-daemon", "reposition", args.connector, str(args.x), str(args.y)], check=True
    )


if __name__ == "__main__":
    main()
