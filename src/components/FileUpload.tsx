import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  uploading: boolean;
  progress: number;
}

export default function FileUpload({ onFilesSelected, uploading, progress }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(Array.from(e.target.files));
    }
  };

  const openFileDialog = () => {
    inputRef.current?.click();
  };

  return (
    <div className="w-full">
      <motion.div
        className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-300 bg-white shadow-md px-6 py-10 ${dragActive ? "border-brand bg-brand/10" : "border-gray-300"}`}
        onClick={openFileDialog}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        initial={{ scale: 1 }}
        animate={{ scale: dragActive ? 1.03 : 1 }}
        whileHover={{ scale: 1.02 }}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          multiple
          onChange={handleChange}
          accept=".pdf,.docx,.md,.tex"
        />
        <span className="text-lg font-semibold text-brand flex items-center gap-2">
          Drag & drop files here
        </span>
        <span className="text-sm text-gray-500 mt-2">or click to select files (.pdf, .docx, .md, .tex)</span>
        <AnimatePresence>
          {uploading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="absolute left-0 bottom-0 w-full px-4 pb-4"
            >
              <div className="w-full bg-gray-200 rounded-full h-3 mt-6">
                <motion.div
                  className="bg-brand h-3 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.4 }}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="block text-xs text-brand mt-1 text-center">Uploading... {progress}%</span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
