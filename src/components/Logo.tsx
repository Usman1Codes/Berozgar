import { motion } from "framer-motion";

const bubbleStyle =
  "inline-block text-[2.7rem] md:text-[4.5rem] font-extrabold leading-none mx-1 px-1 rounded-[1.2rem] shadow-lg bg-gradient-to-b from-brand-light to-brand text-white border-4 border-brand-dark select-none";

const letters = "Berozgar".split("");

// Animation variants
const groupVariants: Record<string, any> = {
  initial: { scale: 0.92, rotate: -2, opacity: 0 },
  animate: {
    scale: 1,
    rotate: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};
const letterVariants: Record<string, any> = {
  initial: { y: 40, scale: 0.8, opacity: 0 },
  animate: (i: number) => ({
    y: [40, 0],
    scale: [0.8, 1.15],
    opacity: 1,
    transition: {
      delay: i * 0.07,
      type: 'spring',
      stiffness: 350,
      damping: 18,
    },
  }),
  hover: {
    scale: 1.25,
    rotate: [0, 12, -12, 0],
    transition: { repeat: Infinity, duration: 1.2 },
  },
};

export default function Logo() {
  // Group animation demo
  return (
    <motion.div
      className="flex items-center space-x-4"
      initial={{ y: 0 }}
      animate={{ y: [0, -18, 0] }}
      transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
    >
      <motion.div
        className="w-16 h-16 md:w-24 md:h-24 bg-brand rounded-full flex items-center justify-center shadow-xl border-4 border-brand-dark"
        initial={{ scale: 0.8, rotate: -10 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 10 }}
      >
        <span className="text-white font-extrabold text-3xl md:text-5xl drop-shadow-lg">B</span>
      </motion.div>
      {/* Group animation, now with per-letter bounce only */}
      <div className="flex">
        {letters.map((l, i) => {
          // Stationary synchronized wave: all letters oscillate in place, phased by index
          const amplitude = 14;
          const phase = (i / (letters.length - 1)) * Math.PI;
          const duration = 2.8;
          return (
            <motion.span
              key={i}
              className={bubbleStyle}
              animate={{ y: [0, -amplitude * Math.sin(phase), 0, amplitude * Math.sin(phase), 0] }}
              transition={{ repeat: Infinity, duration, ease: "easeInOut", delay: 0 }}
              whileHover={{ scale: 1.22 }}
              style={{
                background:
                  i % 2 === 0
                    ? "linear-gradient(180deg, #FF9248 0%, #FF6A00 100%)"
                    : "#111",
                color: "#fff",
                borderColor: i % 2 === 0 ? "#FF6A00" : "#111",
                boxShadow: "0 6px 32px 0 rgba(0,0,0,0.12)",
              }}
            >
              {l}
            </motion.span>
          );
        })}
      </div>
    </motion.div>
  );
}