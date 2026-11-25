import { BLOCKS, DAYS } from "@/shared/constants/schedule";
import type { Cell } from "./api";

export function ScheduleGrid({
  cells,
  onToggle,
  disabled,
}: {
  cells: Cell[];
  onToggle?: (cell: Cell) => void;
  disabled?: boolean;
}) {
  const coordinates = new Map(
    cells.map((cell) => [`${cell.day}:${cell.block}`, cell]),
  );
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[45rem] border-collapse text-center text-sm">
        <caption className="sr-only">Horario semanal</caption>
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
          {BLOCKS.map((block, row) => (
            <tr key={block}>
              <th scope="row" className="border bg-slate-100 p-2">
                {block}
              </th>
              {DAYS.map((day, column) => {
                const cell = coordinates.get(`${column + 1}:${row + 1}`);
                const state = cell?.is_occupied ? "Ocupado" : "Libre";
                const color = cell?.is_occupied
                  ? "bg-blue-100 text-blue-950"
                  : "bg-green-50 text-green-950";
                return (
                  <td key={day} className="border">
                    {cell && onToggle ? (
                      <button
                        type="button"
                        aria-label={`${day} ${block}`}
                        aria-pressed={cell.is_occupied}
                        disabled={disabled}
                        className={`w-full p-2 hover:underline ${color}`}
                        onClick={() => onToggle(cell)}
                      >
                        {state}
                      </button>
                    ) : (
                      <span className={`block p-2 ${color}`}>
                        {cell ? state : "—"}
                      </span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
