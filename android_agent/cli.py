import argparse
import sys
import os
from rich.console import Console
from rich.table import Table

from .device.adb_wrapper import ADBWrapper
from .device.emulator_manager import EmulatorManager
from .device.ui_parser import UIParser
from .agent.core import AndroidAgent
from .utils.visualizer import draw_element_boxes
from .utils.logger import logger

console = Console()

def main():
    parser = argparse.ArgumentParser(
        prog="android-agent",
        description="Autonomous AI Agent operating on Android Emulator and Physical Devices via ADB and Gemini AI."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run an autonomous AI agent task on device/emulator")
    run_parser.add_argument("--task", "-t", required=True, help="Task description (e.g. 'Open Settings and click Display')")
    run_parser.add_argument("--max-steps", type=int, default=15, help="Maximum number of steps (default: 15)")
    run_parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name (default: gemini-2.5-flash)")
    run_parser.add_argument("--serial", "-s", default=None, help="Device serial number")

    # Command: devices
    subparsers.add_parser("devices", help="List connected ADB devices and emulators")

    # Command: emulators
    subparsers.add_parser("emulators", help="List available Android Virtual Devices (AVDs)")

    # Command: start-emulator
    start_emu_parser = subparsers.add_parser("start-emulator", help="Launch an Android Virtual Device")
    start_emu_parser.add_argument("--name", "-n", required=True, help="AVD name to launch")
    start_emu_parser.add_argument("--headless", action="store_true", help="Launch without window UI")

    # Command: screenshot
    ss_parser = subparsers.add_parser("screenshot", help="Capture screenshot from device")
    ss_parser.add_argument("--output", "-o", default="screenshot.png", help="Output PNG filepath")
    ss_parser.add_argument("--annotate", action="store_true", help="Annotate image with UI bounding box badges")

    # Command: dump-ui
    dump_parser = subparsers.add_parser("dump-ui", help="Dump and print current UI element tree")
    dump_parser.add_argument("--serial", "-s", default=None, help="Device serial number")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "devices":
        adb = ADBWrapper()
        devices = adb.get_devices()
        table = Table(title="Connected ADB Devices")
        table.add_column("Serial", style="cyan")
        table.add_column("State", style="green")
        for serial, state in devices:
            table.add_row(serial, state)
        console.print(table)

    elif args.command == "emulators":
        emu = EmulatorManager()
        avds = emu.list_avds()
        table = Table(title="Available Android Virtual Devices (AVDs)")
        table.add_column("AVD Name", style="magenta")
        for avd in avds:
            table.add_row(avd)
        console.print(table)

    elif args.command == "start-emulator":
        emu = EmulatorManager()
        emu.start_emulator(args.name, headless=args.headless)
        console.print(f"[green]Started emulator process for '{args.name}'. Use 'android-agent devices' to verify when booted.[/green]")

    elif args.command == "screenshot":
        adb = ADBWrapper()
        img = adb.screencap()
        if args.annotate:
            xml_dump = adb.dump_hierarchy()
            elements = UIParser.parse_xml(xml_dump, filter_interactive=True)
            elements_dict = [e.to_dict() for e in elements]
            img = draw_element_boxes(img, elements_dict)
        img.save(args.output)
        console.print(f"[green]Saved screenshot to {args.output}[/green]")

    elif args.command == "dump-ui":
        adb = ADBWrapper(serial=args.serial)
        xml_dump = adb.dump_hierarchy()
        elements = UIParser.parse_xml(xml_dump, filter_interactive=True)
        table = Table(title="Parsed UI Elements")
        table.add_column("ID", style="cyan")
        table.add_column("Class", style="yellow")
        table.add_column("Text / Content-Desc", style="white")
        table.add_column("Bounds", style="dim")
        table.add_column("Center", style="green")
        for e in elements:
            label = e.text or e.content_desc or e.resource_id or ""
            table.add_row(str(e.id), e.class_name.split(".")[-1], label, str(e.bounds), str(e.center))
        console.print(table)

    elif args.command == "run":
        agent = AndroidAgent(
            model_name=args.model,
            serial=args.serial
        )
        res = agent.run_task(args.task, max_steps=args.max_steps)
        console.print(f"\n[bold blue]Final Agent Output:[/bold blue] {res}")

if __name__ == "__main__":
    main()
