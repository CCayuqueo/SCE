import { BLOCKS, DAYS } from "@/shared/constants/schedule";
import type { Coordinate, OverlapCell } from "./api";

const scale = [
  { upper: 0, color: "#e0f1df", label: "0 %" },
  { upper: 0.2, color: "#c8e6aa", label: ">0–20 %" },
  { upper: 0.4, color: "#f6e8a0", label: ">20–40 %" },
  { upper: 0.6, color: "#f2bb71", label: ">40–60 %" },
  { upper: 0.8, color: "#de795c", label: ">60–80 %" },
  { upper: 1, color: "#ad303b", label: ">80–100 %" },
];

function selectColor(intensity: number) {
  return scale.find((item) => intensity <= item.upper)?.color ?? scale[5].color;
}

export function Heatmap({
  cells,
  selected,
  onSelect,
}: {
  cells: OverlapCell[];
  selected: Coordinate | null;
  onSelect: (cell: Coordinate) => void;
}) {
  const byCoordinate = new Map(
    cells.map((cell) => [`${cell.day}:${cell.block}`, cell]),
  );
  return (
    <>
      <p className="mb-2 text-sm">
        Color según la proporción de ocupados sobre el total de integrantes.
      </p>
      <ul
        className="mb-4 flex flex-wrap gap-x-4 gap-y-2 text-sm"
        aria-label="Escala de ocupación"
      >
        {scale.map(({ label, color }) => (
          <li key={label} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              style={{ backgroundColor: color }}
              className="h-4 w-4 rounded border border-slate-400"
            />
            {label}
          </li>
        ))}
      </ul>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[45rem] border-collapse text-center text-sm">
          <caption className="sr-only">Mapa de ocupación semanal</caption>
          <thead>
            <tr>
              <th scope="col" className="border bg-slate-100 p-2">
                Bloque
              </th>
              {DAYS.map((day) => (
                <th scope="col" key={day} className="border bg-slate-100 p-2">
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {BLOCKS.map((block, index) => (
              <tr key={block}>
                <th scope="row" className="border bg-slate-100 p-2">
                  {block}
                </th>
                {DAYS.map((day, column) => {
                  const cell = byCoordinate.get(`${column + 1}:${index + 1}`);
                  const active =
                    cell?.day === selected?.day &&
                    cell?.block === selected?.block;
                  return (
                    <td key={day} className="border">
                      {cell && (
                        <button
                          type="button"
                          className="w-full p-2 font-semibold outline-offset-[-3px] focus-visible:outline-2 aria-pressed:underline aria-pressed:outline-2"
                          style={{
                            backgroundColor: selectColor(cell.intensity),
                            color: cell.intensity > 0.8 ? "white" : "#0f172a",
                          }}
                          aria-label={`${day} ${block}: ${cell.weight} ocupados, ${cell.available_count} disponibles, ${cell.pending_count} pendientes`}
                          aria-pressed={active}
                          onClick={() =>
                            onSelect({ day: cell.day, block: cell.block })
                          }
                        >
                          {cell.weight}
                        </button>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
