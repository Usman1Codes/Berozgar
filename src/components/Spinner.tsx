import { motion } from 'framer-motion';

export default function Spinner() {
  return (
    <motion.div
      className="w-12 h-12 border-4 border-t-brand border-gray-300 rounded-full"
      animate={{ rotate: 360 }}
      transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
    />
  );
}