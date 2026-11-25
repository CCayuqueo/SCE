import { useEffect, useRef, useState } from "react";

function ImagePreview({ file }: { file: File }) {
  const image = useRef<HTMLImageElement>(null);
  useEffect(() => {
    const url = URL.createObjectURL(file);
    if (image.current) image.current.src = url;
    return () => URL.revokeObjectURL(url);
  }, [file]);
  return (
    <img
      ref={image}
      className="mt-3 max-h-64 max-w-full rounded border object-contain"
      alt="Vista previa de la captura seleccionada"
    />
  );
}

export function ImageSelection({
  maxBytes,
  disabled,
  onSelect,
  file,
}: {
  maxBytes: number;
  disabled: boolean;
  onSelect: (file: File | null) => void;
  file: File | null;
}) {
  const [error, setError] = useState("");
  return (
    <>
      <label className="block" htmlFor="capture">
        Captura del horario
      </label>
      <input
        id="capture"
        className="mt-1 block max-w-full"
        type="file"
        accept=".png,.jpg,.jpeg,image/png,image/jpeg"
        disabled={disabled}
        onChange={(event) => {
          const selected = event.target.files?.[0] ?? null;
          let message = "";
          if (selected) {
            const compatible = selected.type
              ? ["image/png", "image/jpeg"].includes(selected.type)
              : /\.(png|jpe?g)$/i.test(selected.name);
            if (!compatible) message = "Selecciona un archivo PNG o JPEG.";
            else if (!selected.size || selected.size > maxBytes)
              message = "El archivo está vacío o supera el tamaño permitido.";
          }
          setError(message);
          if (message) event.target.value = "";
          onSelect(message ? null : selected);
        }}
      />
      <p className="mt-2 text-sm text-slate-700">
        PNG recomendado. También puedes usar un JPEG compatible. Límite de{" "}
        {maxBytes / 1024 ** 2} MiB.
      </p>
      {error && (
        <p role="alert" className="mt-2 text-red-800">
          {error}
        </p>
      )}
      {file && <ImagePreview key={file.name + file.lastModified} file={file} />}
    </>
  );
}
