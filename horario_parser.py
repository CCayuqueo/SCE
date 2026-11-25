"""Extrae bloques de horarios digitales mediante visión clásica, sin OCR."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
ESTADOS = ("tope", "inscrita", "pre-inscrita", "libre")
# Colores medidos en las capturas, en la representación LAB de OpenCV.
REFERENCIAS = np.array([[159, 183, 199], [184, 158, 205],
                        [226, 118, 144], [255, 128, 128]], dtype=np.float32)
EXTENSIONES = {".png", ".jpg", ".jpeg", ".webp"}


def _grupos(indices: np.ndarray) -> list[np.ndarray]:
    if len(indices) == 0:
        return []
    return np.split(indices, np.where(np.diff(indices) > 1)[0] + 1)


def _geometria(im: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w = im.shape[:2]
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    azul = cv2.inRange(hsv, (95, 150, 25), (110, 255, 120))
    perfil = np.count_nonzero(azul, axis=1)
    filas = _grupos(np.flatnonzero(perfil > max(w * .25, perfil.max() * .65)))
    if not filas:
        raise ValueError("No se encontró el encabezado azul de la tabla")
    cab = max(filas, key=lambda g: perfil[g].sum())
    columnas = np.count_nonzero(azul[cab[0]:cab[-1] + 1], axis=0)
    activos = np.flatnonzero(columnas > len(cab) * .4)
    if len(activos) < w * .25:
        raise ValueError("Encabezado incompleto")
    izquierda, derecha = max(0, int(activos[0]) - 1), min(w - 1, int(activos[-1]) + 1)
    # Las líneas son grises y continuas; la apertura elimina letras y ruido.
    gris = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    maximo = im.max(axis=2).astype(np.int16)
    minimo = im.min(axis=2).astype(np.int16)
    mascara = (((maximo - minimo) < 12) & (gris > 90) & (gris < 210)).astype(np.uint8) * 255
    horizontal = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, (derecha - izquierda) // 12), 1)))
    p = np.count_nonzero(horizontal[:, izquierda:derecha + 1], axis=1)
    candidatos = [int(round(g.mean())) for g in _grupos(np.flatnonzero(p > (derecha - izquierda) * .55))]
    candidatos = [y for y in candidatos if y >= cab[0] - max(3, len(cab))]
    if len(candidatos) < 12:
        raise ValueError("No se encontraron las 12 fronteras horizontales")
    # La primera línea es el borde superior y la segunda el fin del encabezado.
    superiores = [y for y in candidatos if y <= cab[0]]
    inicio = min(superiores, key=lambda y: abs(y - cab[0])) if superiores else max(0, int(cab[0]) - 1)
    posteriores = [y for y in candidatos if y > cab[-1]]
    if len(posteriores) < 11:
        raise ValueError("Tabla incompleta: faltan filas")
    ys = np.array([inicio] + posteriores[:11])
    pasos = np.diff(ys[1:])
    if np.max(np.abs(pasos - np.median(pasos))) > max(2, np.median(pasos) * .15):
        raise ValueError("Espaciado de filas irregular")
    vertical = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(3, int(np.median(pasos) * .6)))))
    vp = np.count_nonzero(vertical[ys[1]:ys[-1] + 1], axis=0)
    grupos = _grupos(np.flatnonzero(vp > (ys[-1] - ys[1]) * .55))
    xs = [int(round(g.mean())) for g in grupos if izquierda - 2 <= g.mean() <= derecha + 2]
    if len(xs) != 9:
        raise ValueError(f"Se esperaban 9 fronteras verticales; se encontraron {len(xs)}")
    return np.array(xs), ys


def _calibrar(lab: np.ndarray, ys: np.ndarray, xs: np.ndarray) -> tuple[bool, np.ndarray]:
    region = lab[ys[-1] + 1:, xs[0]:xs[-1] + 1].astype(np.float32)
    if not region.size:
        return False, REFERENCIAS.copy()
    # Cada muestra de la leyenda es un rectángulo horizontal relleno.
    refs = REFERENCIAS.copy()
    encontrados = []
    for i, ref in enumerate(REFERENCIAS[:3]):
        distancia = np.linalg.norm(region - ref, axis=2)
        mask = (distancia < 15).astype(np.uint8)
        n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(mask)
        candidatos = [j for j in range(1, n) if stats[j, cv2.CC_STAT_WIDTH] > (xs[-1] - xs[0]) * .025 and stats[j, cv2.CC_STAT_HEIGHT] >= 3 and stats[j, cv2.CC_STAT_AREA] > 30]
        if candidatos:
            j = max(candidatos, key=lambda k: stats[k, cv2.CC_STAT_AREA])
            refs[i] = np.median(region[etiquetas == j], axis=0)
            encontrados.append(j)
    # Blanco es el fondo de las celdas libres y de la muestra libre.
    return len(encontrados) == 3, refs


def parse_horario(image_path: str) -> dict:
    """Devuelve los bloques ocupados de una captura; falla ante una grilla ilegible."""
    path = Path(image_path)
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None:
        raise ValueError(f"No se puede leer la imagen: {path}")
    xs, ys = _geometria(im)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
    leyenda, refs = _calibrar(lab, ys, xs)
    horarios = []
    for dia, nombre in enumerate(DIAS):
        x0, x1 = xs[dia + 1:dia + 3]
        dx = max(1, round((x1 - x0) * .13))
        for bloque in range(10):
            y0, y1 = ys[bloque + 1:bloque + 3]
            dy = max(1, round((y1 - y0) * .13))
            muestra = lab[y0 + dy:y1 - dy, x0 + dx:x1 - dx]
            if not muestra.size:
                raise ValueError("Celda demasiado pequeña")
            color = np.median(muestra.reshape(-1, 3), axis=0)
            distancias = np.linalg.norm(refs - color, axis=1)
            estado = ESTADOS[int(np.argmin(distancias))]
            if distancias.min() > 35:
                raise ValueError(f"Color de celda desconocido en {nombre}, bloque {bloque + 1}")
            if estado != "libre":
                horarios.append({"dia": nombre, "bloque": f"{2 * bloque + 1}-{2 * bloque + 2}", "estado": estado, "materia": None})
    return {"archivo": path.name, "dimensiones": {"ancho": im.shape[1], "alto": im.shape[0]}, "leyenda_detectada": leyenda, "horarios": horarios}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ruta", help="Imagen o carpeta de imágenes")
    args = parser.parse_args()
    path = Path(args.ruta)
    try:
        if path.is_dir():
            archivos = sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONES)
            if not archivos:
                raise ValueError("La carpeta no contiene imágenes compatibles")
            resultado = [parse_horario(str(p)) for p in archivos]
        else:
            resultado = parse_horario(str(path))
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    except ValueError as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
