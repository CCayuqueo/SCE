"""Ejecuta el parser determinista con límites antes de importar OpenCV."""

import json
import resource
import runpy
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def main() -> int:
    image_path, cpu_limit = sys.argv[1:]
    memory = 2 * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    seconds = int(cpu_limit)
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds + 1))
    parser = BACKEND / "horario_parser.py"
    if not parser.is_file():
        parser = BACKEND.parent / "horario_parser.py"
    parse_horario = runpy.run_path(str(parser))["parse_horario"]
    try:
        result = parse_horario(image_path)
    except ValueError:
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
