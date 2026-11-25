import { useEffect, useRef, type ReactNode } from "react";

export function RoomDialog({
  title,
  children,
  busy,
  onClose,
}: {
  title: string;
  children: ReactNode;
  busy: boolean;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-labelledby="room-dialog-title"
      className="m-auto w-[min(32rem,94vw)] rounded p-6 backdrop:bg-black/50"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <h2 id="room-dialog-title" className="mb-4 text-xl font-bold">
        {title}
      </h2>
      {children}
      <button
        type="button"
        className="mt-4 underline"
        disabled={busy}
        onClick={onClose}
      >
        Cancelar
      </button>
    </dialog>
  );
}
