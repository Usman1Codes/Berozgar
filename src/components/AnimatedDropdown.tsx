import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const options = [
  "Fresher",
  "Experienced",
  "Manager",
  "Intern",
  "Freelancer",
];

export default function AnimatedDropdown() {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(options[0]);

  return (
    <div className="relative w-full max-w-xs mx-auto">
      <button
        type="button"
        className="w-full px-4 py-3 bg-white rounded-lg border border-gray-300 shadow-sm flex justify-between items-center font-semibold text-gray-800 hover:bg-brand-light focus:outline-none focus:ring-4 focus:ring-brand/40 transition"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span>{selected}</span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          className="ml-2 text-lg"
        >
          ▼
        </motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.ul
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
            className="absolute z-10 mt-2 w-full bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden"
            role="listbox"
          >
            {options.map((option) => (
              <motion.li
                key={option}
                onClick={() => {
                  setSelected(option);
                  setOpen(false);
                }}
                className={`px-4 py-3 cursor-pointer text-gray-800 hover:bg-brand-light transition ${selected === option ? 'bg-brand-light font-bold' : ''}`}
                whileHover={{ scale: 1.04, x: 6 }}
                role="option"
                aria-selected={selected === option}
              >
                {option}
              </motion.li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
