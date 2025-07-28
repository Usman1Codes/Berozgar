import { useRef } from "react";

interface DrivePickerProps {
  label: string;
  onFilePicked: (file: { id: string; name: string }) => void;
  pickedFile?: { id: string; name: string };
  disabled?: boolean;
}

export default function DrivePicker({ label, onFilePicked, pickedFile, disabled }: DrivePickerProps) {
  // This is a stub for Google Drive Picker integration.
  // Replace with actual picker logic as per your backend/frontend integration.
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        className="px-3 py-2 bg-brand-light text-white rounded hover:bg-brand-dark disabled:opacity-50"
        disabled={disabled}
        onClick={() => {
          // Simulate picking a file (replace with Drive picker logic)
          const fakeFile = { id: Math.random().toString(36).slice(2), name: label + " Example.pdf" };
          onFilePicked(fakeFile);
        }}
      >
        Pick from Drive
      </button>
      {pickedFile && (
        <span className="text-sm text-gray-700 dark:text-gray-200">{pickedFile.name}</span>
      )}
    </div>
  );
}
