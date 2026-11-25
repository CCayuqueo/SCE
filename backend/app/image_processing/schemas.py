from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Positive = Annotated[int, Field(gt=0)]


class Dimensions(BaseModel):
    model_config = ConfigDict(strict=True)

    ancho: Positive
    alto: Positive


class DetectedCell(BaseModel):
    model_config = ConfigDict(strict=True)

    dia: str
    bloque: str
    estado: str
    materia: str | None = None


class ParserResult(BaseModel):
    model_config = ConfigDict(strict=True)

    dimensiones: Dimensions
    horarios: Annotated[list[DetectedCell], Field(max_length=70)]
