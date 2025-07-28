import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface OutputFile {
  name: string;
  url: string;
  type: string;
}

interface OutputResultProps {
  files: OutputFile[];
  onEmail: (email: string) => Promise<void>;
  emailing: boolean;
  emailError: string | null;
  emailSuccess: boolean;
}

export default function OutputResult({ files, onEmail, emailing, emailError, emailSuccess }: OutputResultProps) {
  const [show, setShow] = useState(true);
  const [email, setEmail] = useState("");

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="bg-white dark:bg-[#23232b] rounded-2xl shadow-2xl p-8 max-w-lg w-full relative flex flex-col items-center"
            initial={{ scale: 0.92, y: 40, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 40, opacity: 0 }}
            transition={{ type: "spring", stiffness: 200, damping: 22 }}
          >
            <button
              className="absolute top-4 right-4 text-gray-500 hover:text-brand text-xl"
              onClick={() => setShow(false)}
              aria-label="Close results"
            >
              ×
            </button>
            <h2 className="text-2xl font-bold mb-4 text-brand">Your Documents Are Ready!</h2>
            <div className="w-full flex flex-col gap-3 mb-6">
              {files.map((file) => (
                <a
                  key={file.url}
                  href={file.url}
                  download={file.name}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 rounded-lg bg-gray-100 dark:bg-[#282832] hover:bg-brand/10 transition border border-gray-200 dark:border-[#333]"
                >
                  <span className="font-semibold text-gray-800 dark:text-gray-100">{file.name}</span>
                  <span className="ml-auto text-xs px-2 py-1 rounded bg-brand text-white">Download</span>
                </a>
              ))}
            </div>
            <form
              className="w-full flex flex-col gap-2"
              onSubmit={async (e) => {
                e.preventDefault();
                if (email) await onEmail(email);
              }}
            >
              <label className="text-sm font-medium text-gray-700 dark:text-gray-200">Send to Email</label>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="flex-1 px-3 py-2 rounded border border-gray-300 dark:bg-[#23232b] dark:text-white"
                  required
                />
                <button
                  type="submit"
                  disabled={emailing}
                  className="px-4 py-2 rounded bg-brand text-white hover:bg-brand-dark transition"
                >
                  {emailing ? "Sending..." : "Send"}
                </button>
              </div>
              {emailError && <span className="text-sm text-red-500">{emailError}</span>}
              {emailSuccess && <span className="text-sm text-green-600">Email sent!</span>}
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
