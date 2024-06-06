import argparse
import sys
import logging


def urlopen(path, mode="r"):
    if path == "-":
        if mode == "w":
            return sys.stdout
        return sys.stdin
    return open(path, mode=mode)

    # {
    #     'type': '',
    #     'label': '',
    #     'reference': '',
    #     'package': '',
    #     'manufacturer': {
    #         'name': '',
    #         'url': '',
    #         'reference': '',
    #     },
    #     'digikey': {
    #         'url': '',
    #         'part_number': ''
    #     },
    # }


def parse_kicad_component(component):
    def parse_component_data(component_info):
        fucked_list = ["R"]

        data = {
            "type": "",
            "label": "",
            "reference": "",
            "package": "",
            "manufacturer": {
                "name": "",
                "url": "",
                "reference": "",
            },
            "digikey": {"url": "", "part_number": ""},
        }

        for info in component_info:
            if info[0] == "L":
                data["type"] = info[1]
                data["label"] = info[2]
                continue

            if info[0] == "F":
                if info[1] == "0":
                    data["label"] = info[2]
                    continue

                if info[1] == "1":
                    data["reference"] = info[2]
                    continue

                if info[1] == "2":
                    data["package"] = info[2]
                    continue

                if info[1] == "3":
                    data["manufacturer"]["url"] = info[2]
                    continue

                if info[1] == "4":
                    if data["type"][-1:] in fucked_list:
                        data["manufacturer"]["reference"] = info[2]
                    else:
                        data["manufacturer"]["name"] = info[2]
                    continue

                if info[1] == "5":
                    if data["type"][-1:] in fucked_list:
                        data["manufacturer"]["name"] = info[2]
                    else:
                        data["manufacturer"]["reference"] = info[2]
                    continue

                if info[1] == "6":
                    if data["type"][-1:] in fucked_list:
                        data["digikey"]["part_number"] = info[2]
                    else:
                        data["digikey"]["url"] = info[2]
                    continue

                if info[1] == "7":
                    if data["type"][-1:] in fucked_list:
                        data["digikey"]["url"] = info[2]
                    else:
                        data["digikey"]["part_number"] = info[2]
                    continue

        return data

    def parse_type(component):
        if component["type"] == "Device:R":
            component["type"] = "Resistor"
        if component["type"] == "Device:C":
            component["type"] = "Capacitor"
        if component["type"] == "Device:LED":
            component["type"] = "LED"
        if component["type"] == "Device:D":
            component["type"] = "Diode"
        return component

    comp_info = component.split("\n")
    comp_info = [c.split(" ") for c in comp_info]
    comp_info = [[s.replace('"', "") for s in c] for c in comp_info]
    comp_info = parse_component_data(comp_info)
    comp_info = parse_type(comp_info)

    return comp_info


def main(args):
    logger = logging.getLogger(__name__)
    logger.info("start reading")

    all_components = []

    for file in args.schematics:
        with urlopen(file) as fi:
            file_content = fi.read()

        components = file_content.split("$Comp\n")
        components = [c.strip() for c in components]
        components = [c for c in components if c.endswith("$EndComp")]
        components = [c.replace("\n$EndComp", "") for c in components]
        components = [parse_kicad_component(c) for c in components]
        components = [c for c in components if not c["label"].startswith("#")]

        all_components.extend(components)
    
    all_components = sorted(all_components, key=lambda c: c['label'])

    with urlopen(args.output, mode='w') as fo:
        # header
        print(
            args.delimiter.join(
                [
                    "type",
                    "label",
                    "reference",
                    "package",
                    "manufacturer_name",
                    "manufacturer_url",
                    "manufacturer_reference",
                ]
            ),
            file=fo,
        )

        # content
        for c in all_components:
            print(
                args.delimiter.join(
                    [
                        c["type"],
                        c["label"],
                        c["reference"],
                        c["package"],
                        c["manufacturer"]["name"],
                        c["manufacturer"]["url"],
                        c["manufacturer"]["reference"],
                    ]
                ),
                file=fo,
            )

    logger.info("done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kicad parser for component list")

    parser.add_argument("schematics", nargs="+", type=str, help="schematic file URL")
    parser.add_argument("output", type=str, help="CSV file output")
    parser.add_argument("--delimiter", type=str, default=",", help="CSV delimiter")

    args = parser.parse_args()
    main(args)
