import { useRef, useState } from 'react';
import { motion, useViewportScroll, useTransform, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import Logo from './components/Logo';
import Spinner from './components/Spinner';
import FileUpload from './components/FileUpload';
import AnimatedDropdown from './components/AnimatedDropdown';
import DrivePicker from './components/DrivePicker';
import OutputResult from './components/OutputResult';

// Helper: Laughing/Mock Face SVG (classic)
function laughingFaceSVG({ size, color }: { size: number; color: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="48" fill={color} stroke="#222" strokeWidth="4" />
      {/* Eyes */}
      <ellipse cx="35" cy="45" rx="7" ry="10" fill="#fff" stroke="#222" strokeWidth="2" />
      <ellipse cx="65" cy="45" rx="7" ry="10" fill="#fff" stroke="#222" strokeWidth="2" />
      {/* Pupils */}
      <ellipse cx="35" cy="48" rx="2.5" ry="4" fill="#222" />
      <ellipse cx="65" cy="48" rx="2.5" ry="4" fill="#222" />
      {/* Eyebrows (mocking tilt) */}
      <rect x="28" y="34" width="14" height="3" rx="1.5" fill="#222" transform="rotate(-15 28 34)" />
      <rect x="58" y="34" width="14" height="3" rx="1.5" fill="#222" transform="rotate(15 58 34)" />
      {/* Big Laughing Mouth */}
      <ellipse cx="50" cy="68" rx="22" ry="13" fill="#fff" stroke="#222" strokeWidth="3" />
      <ellipse cx="50" cy="71" rx="15" ry="7" fill="#FF6A00" stroke="#222" strokeWidth="2" />
      {/* Tongue */}
      <ellipse cx="50" cy="74" rx="6" ry="3" fill="#fff" fillOpacity="0.8" />
      {/* Tears of laughter */}
      <ellipse cx="22" cy="60" rx="3" ry="6" fill="#fff" stroke="#FF9248" strokeWidth="1.5" />
      <ellipse cx="78" cy="60" rx="3" ry="6" fill="#fff" stroke="#FF9248" strokeWidth="1.5" />
    </svg>
  );
}

// Helper: Laughing/Mock Face SVG (variant)
function laughingFaceSVG2({ size, color }: { size: number; color: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="50" cy="52" rx="48" ry="44" fill={color} stroke="#222" strokeWidth="4" />
      {/* Eyes: squinting laughter */}
      <path d="M32 44 Q36 40 40 44" stroke="#222" strokeWidth="3" strokeLinecap="round"/>
      <path d="M60 44 Q64 40 68 44" stroke="#222" strokeWidth="3" strokeLinecap="round"/>
      {/* Eyebrows */}
      <rect x="26" y="34" width="14" height="3" rx="1.5" fill="#222" transform="rotate(-10 26 34)" />
      <rect x="60" y="34" width="14" height="3" rx="1.5" fill="#222" transform="rotate(10 60 34)" />
      {/* Big Open Laughing Mouth */}
      <ellipse cx="50" cy="70" rx="20" ry="12" fill="#fff" stroke="#222" strokeWidth="3" />
      <ellipse cx="50" cy="73" rx="13" ry="6" fill="#FF9248" stroke="#222" strokeWidth="2" />
      {/* Tongue */}
      <ellipse cx="50" cy="76" rx="6" ry="2.5" fill="#fff" fillOpacity="0.7" />
      {/* Cheek blush */}
      <ellipse cx="28" cy="62" rx="4" ry="2" fill="#FF6A00" fillOpacity="0.4" />
      <ellipse cx="72" cy="62" rx="4" ry="2" fill="#FF6A00" fillOpacity="0.4" />
    </svg>
  );
}

// Helper: Pointing Hand SVG (right)
function pointingHandSVG({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="20" y="40" width="40" height="20" rx="10" fill="#fff" stroke="#222" strokeWidth="3" />
      <rect x="54" y="34" width="16" height="12" rx="6" fill="#FF6A00" stroke="#222" strokeWidth="2" />
      <rect x="60" y="28" width="10" height="8" rx="4" fill="#FF9248" stroke="#222" strokeWidth="2" />
      {/* Index finger */}
      <rect x="66" y="22" width="8" height="22" rx="4" fill="#fff" stroke="#222" strokeWidth="3" />
      {/* Knuckle lines */}
      <rect x="28" y="56" width="6" height="2" rx="1" fill="#FF9248" />
      <rect x="36" y="56" width="6" height="2" rx="1" fill="#FF9248" />
      <rect x="44" y="56" width="6" height="2" rx="1" fill="#FF9248" />
    </svg>
  );
}

interface OutputFile {
  name: string;
  url: string;
  type: string;
}

export default function App() {
  // Resume
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [resumeDriveFile, setResumeDriveFile] = useState<{id: string, name: string} | null>(null);
  const [resumeError, setResumeError] = useState<string | null>(null);
  // Job Description
  const [jobDescText, setJobDescText] = useState("");
  const [jobDescFiles, setJobDescFiles] = useState<File[]>([]);
  const [jobDescDriveFile, setJobDescDriveFile] = useState<{id: string, name: string} | null>(null);
  const [jobDescUrl, setJobDescUrl] = useState("");
  const [jobDescError, setJobDescError] = useState<string | null>(null);
  // Experience
  const [expFiles, setExpFiles] = useState<File[]>([]);
  const [expDriveFile, setExpDriveFile] = useState<{id: string, name: string} | null>(null);
  const [expError, setExpError] = useState<string | null>(null);
  // Project Readmes
  const [readmeFiles, setReadmeFiles] = useState<File[]>([]);
  const [readmeDriveFile, setReadmeDriveFile] = useState<{id: string, name: string} | null>(null);
  const [readmeError, setReadmeError] = useState<string | null>(null);
  // General form error
  const [formError, setFormError] = useState<string | null>(null);
  // Output/result state
  const [outputFiles, setOutputFiles] = useState<OutputFile[]>([]);
  const [emailing, setEmailing] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuccess, setEmailSuccess] = useState(false);

  const [heroExited, setHeroExited] = useState(false);
  const [inputEntered, setInputEntered] = useState(false);

  // Seamless scroll handler
  const handleSeamlessScroll = () => {
    setHeroExited(true);
    setTimeout(() => {
      setInputEntered(true);
      inputRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 650); // Match animation duration
  }
  const inputRef = useRef<HTMLDivElement>(null);
  const { scrollY } = useViewportScroll();
  const y1 = useTransform(scrollY, [0, 500], [0, -100]);

  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Reusable card wrapper
  const Section: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      whileHover={{ scale: 1.02 }}
      className="space-y-2"
    >
      {children}
    </motion.div>
  );

  const scrollToInput = () => {
    inputRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async () => {
    setJobDescError(null);
    setResumeError(null);
    setFormError(null);
    if (resumeFiles.length === 0) {
      setResumeError("Please upload at least one resume file.");
      return;
    }
    // Only one JD input allowed
    const jdModes = [jobDescFiles.length > 0, !!jobDescUrl, !!jobDescText].filter(Boolean);
    if (jdModes.length > 1) {
      setJobDescError("Please provide only one job description input (file, URL, or text). Clear the others.");
      return;
    }
    setLoading(true);
    setUploadProgress(0);
    try {
      let jdUrlResult = null;
      // If URL mode, call /api/jd_from_url first
      if (jobDescUrl) {
        try {
          jdUrlResult = await axios.post("http://localhost:8001/api/jd_from_url", { url: jobDescUrl });
        } catch (e: any) {
          setJobDescError("Failed to fetch job description from URL.");
          setLoading(false);
          return;
        }
      }
      const formData = new FormData();
      resumeFiles.forEach((file) => {
        formData.append("resume_files", file);
      });
      if (jobDescFiles.length > 0) {
        formData.append("jd_file", jobDescFiles[0]); // Only first file supported for JD
      } else if (jobDescText) {
        formData.append("jd_text", jobDescText);
      } // If URL mode, do NOT send jd_text or jd_file; backend will pick up job_description_url.txt

      if (expFiles.length > 0) {
        expFiles.forEach((file) => {
          formData.append("exp_files", file);
        });
      }
      if (readmeFiles.length > 0) {
        readmeFiles.forEach((file) => {
          formData.append("readme_files", file);
        });
      }
      const response = await axios.post("http://localhost:8001/api/submit", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) {
            setUploadProgress(Math.round((e.loaded * 100) / e.total));
          }
        },
      });
      setResumeError(null);
      setJobDescError(null);
      setFormError(null);
      alert(`Upload successful. Resumes: ${response.data.resume_files.join(", ")}, Experience: ${response.data.exp_files.join(", ")}, Readmes: ${response.data.readme_files.join(", ")}, JD: ${(response.data.jd_files || []).join(", ")}`);
    } catch (e: any) {
      console.error(e);
      if (e.response && e.response.data && e.response.data.detail) {
        setFormError(e.response.data.detail);
      } else {
        setFormError("Upload failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-[#18181b]">
      {/* Hero Section */}
      <motion.section className="relative h-screen overflow-hidden">
        <motion.div
  style={{ y: y1 }}
  className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-background-dark via-brand-dark to-brand flex items-center justify-center overflow-hidden"
>
  {/* Animated Laughing/Mock Faces */}
  {/* Top Left */}
  <motion.div
    className="absolute top-10 left-10 z-0"
    initial={{ rotate: -10, y: 0 }}
    animate={{ rotate: [ -10, 5, -10 ], y: [0, 20, 0] }}
    transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
  >
    {laughingFaceSVG({ size: 90, color: "#FF6A00" })}
  </motion.div>
  {/* Top Right (classic) */}
  <motion.div
    className="absolute top-24 right-24 z-0"
    initial={{ rotate: 8, y: 0 }}
    animate={{ rotate: [8, -8, 8], y: [0, -18, 0] }}
    transition={{ repeat: Infinity, duration: 7, ease: "easeInOut" }}
  >
    {laughingFaceSVG({ size: 70, color: "#FF9248" })}
  </motion.div>
  {/* Top Right (variant) */}
  <motion.div
    className="absolute top-44 right-56 z-0"
    initial={{ rotate: -8, x: 0 }}
    animate={{ rotate: [-8, 8, -8], x: [0, 16, 0] }}
    transition={{ repeat: Infinity, duration: 9, ease: "easeInOut" }}
  >
    {laughingFaceSVG2({ size: 80, color: "#fff" })}
  </motion.div>
  {/* Bottom Left (classic) */}
  <motion.div
    className="absolute bottom-16 left-32 z-0"
    initial={{ rotate: 0, x: 0 }}
    animate={{ rotate: [0, 12, 0], x: [0, 22, 0] }}
    transition={{ repeat: Infinity, duration: 9, ease: "easeInOut" }}
  >
    {laughingFaceSVG({ size: 100, color: "#fff" })}
  </motion.div>
  {/* Bottom Left (variant) */}
  <motion.div
    className="absolute bottom-32 left-16 z-0"
    initial={{ scale: 1, y: 0 }}
    animate={{ scale: [1, 1.12, 1], y: [0, -18, 0] }}
    transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
  >
    {laughingFaceSVG2({ size: 90, color: "#FF6A00" })}
  </motion.div>
  {/* Bottom Right (classic) */}
  <motion.div
    className="absolute bottom-20 right-10 z-0"
    initial={{ rotate: -6, y: 0 }}
    animate={{ rotate: [-6, 6, -6], y: [0, 16, 0] }}
    transition={{ repeat: Infinity, duration: 10, ease: "easeInOut" }}
  >
    {laughingFaceSVG({ size: 120, color: "#FF6A00" })}
  </motion.div>
  {/* Bottom Right (variant) */}
  <motion.div
    className="absolute bottom-36 right-32 z-0"
    initial={{ scale: 1, x: 0 }}
    animate={{ scale: [1, 1.09, 1], x: [0, -16, 0] }}
    transition={{ repeat: Infinity, duration: 7, ease: "easeInOut" }}
  >
    {laughingFaceSVG2({ size: 70, color: "#FF9248" })}
  </motion.div>
  {/* Top Center Floating (classic, now moving horizontally) */}
  <motion.div
    className="absolute left-1/2 top-20 z-0 -translate-x-1/2"
    initial={{ scale: 0.95, rotate: 0, x: -30 }}
    animate={{ scale: [0.95, 1.1, 0.95], rotate: [0, 8, 0], x: [ -30, 30, -30 ] }}
    transition={{ repeat: Infinity, duration: 14, ease: "easeInOut" }}
  >
    {laughingFaceSVG({ size: 140, color: "#FF9248" })}
  </motion.div>
  {/* Center Floating (variant) */}
  <motion.div
    className="absolute left-1/2 top-2/3 z-0 -translate-x-1/2"
    initial={{ scale: 1, rotate: 0 }}
    animate={{ scale: [1, 1.13, 1], rotate: [0, -8, 0] }}
    transition={{ repeat: Infinity, duration: 10, ease: "easeInOut" }}
  >
    {laughingFaceSVG2({ size: 110, color: "#fff" })}
  </motion.div>
  {/* Pointing Hand Emojis */}
  <motion.div
    className="absolute left-1/2 top-1/4 z-0"
    initial={{ rotate: -20, y: 0 }}
    animate={{ rotate: [-20, 10, -20], y: [0, 18, 0] }}
    transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
  >
    {pointingHandSVG({ size: 54 })}
  </motion.div>
  <motion.div
    className="absolute right-1/3 bottom-1/3 z-0"
    initial={{ rotate: 15, x: 0 }}
    animate={{ rotate: [15, -15, 15], x: [0, 10, 0] }}
    transition={{ repeat: Infinity, duration: 9, ease: "easeInOut" }}
  >
    {pointingHandSVG({ size: 60 })}
  </motion.div>
  {/* Helper: Laughing Face SVG */}

  <motion.div
    className="absolute right-20 bottom-10 md:right-40 md:bottom-24 z-10"
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 0.9, scale: 1 }}
    transition={{ duration: 2, delay: 1 }}
  >
    {/* Swap this placeholder for an actual AI-generated SVG or image */}
    <svg width="160" height="160" viewBox="0 0 160 160" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="20" y="40" width="120" height="80" rx="20" fill="#fff" fillOpacity="0.12"/>
      <rect x="36" y="56" width="88" height="48" rx="12" fill="#FF6A00" fillOpacity="0.25"/>
      <rect x="48" y="68" width="64" height="24" rx="6" fill="#fff" fillOpacity="0.7"/>
      <circle cx="80" cy="120" r="10" fill="#FF6A00" fillOpacity="0.7"/>
      <circle cx="80" cy="120" r="5" fill="#fff" fillOpacity="0.8"/>
    </svg>
  </motion.div>
  {/* Animated blur blob for depth */}
  <motion.div
    initial={{ opacity: 0, scale: 0.8 }}
    animate={{ opacity: 0.3, scale: 1 }}
    transition={{ duration: 2 }}
    className="w-[60vw] h-[60vw] max-w-[900px] max-h-[900px] rounded-full bg-brand opacity-30 blur-3xl absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
  />
</motion.div>
        <div className="relative z-10 flex flex-col items-center justify-center h-full text-center px-6">
          <Logo />
          <motion.h1
  initial={{ opacity: 0, y: -20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 1 }}
  className="text-4xl md:text-6xl font-bold mt-4"
>
  Berozgar
</motion.h1>
<motion.h2
  className="mt-8 mb-4 text-3xl md:text-5xl font-extrabold text-white text-center relative inline-block cursor-pointer"
  initial={{ opacity: 0, scale: 0.85 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{ type: "spring", stiffness: 180, damping: 16, delay: 0.2 }}
  whileHover={{ scale: 1.09, textShadow: "0 0 32px #FF9248, 0 0 16px #fff" }}
  style={{
    background: "linear-gradient(90deg, #FF9248 0%, #FF6A00 45%, #FF6A00 55%, #FF9248 100%)",
    backgroundClip: "text",
    WebkitBackgroundClip: "text",
    color: "transparent",
    WebkitTextFillColor: "black",
    animation: "shimmer 2.5s infinite linear"
  }}
>
  Turning Your Unemployment into a Full-Time Job Application
</motion.h2>
<motion.div
  className="mt-6 mb-2 flex flex-col items-center cursor-pointer select-none"
  initial={{ opacity: 0, y: 30, rotate: -8 }}
  animate={{ opacity: 1, y: [30, 0, 10, 0], rotate: [-8, 8, -8], transition: { duration: 2.8, repeat: Infinity, repeatType: 'reverse', ease: 'easeInOut' } }}
  whileHover={{ scale: 1.13, filter: 'brightness(1.15)' }}
  onClick={handleSeamlessScroll}
  title="Something's waiting below..."
>
  {/* You can keep any animated/graphic content here if needed */}
</motion.div>
<div className="flex flex-col items-center" style={{ marginTop: '-38px' }}>
  <button
    onClick={handleSeamlessScroll}
    className="px-7 py-3 bg-brand text-white rounded-full font-bold text-lg shadow-lg hover:bg-brand-dark focus:outline-none focus:ring-4 focus:ring-brand/50 transition-transform duration-400 ease-out hover:-translate-y-2 hover:-rotate-3"
    type="button"
    aria-label="Scroll to form section"
  >
    Duba dy Bhai
  </button>
</div>
<style>{`
@keyframes shimmer {
  0% { background-position: -600px 0; }
  100% { background-position: 600px 0; }
}
.m-hero-tagline {
  background-size: 200% auto;
  animation: shimmer 2.5s linear infinite;
}
`}</style>

        </div>
      </motion.section>

      {/* Input Section */}
      <motion.section
        ref={inputRef}
        className="relative min-h-screen flex items-center justify-center bg-background-light text-gray-900 px-4 py-20 overflow-hidden"
        initial={{ opacity: 0, scale: 0.98 }}
        animate={inputEntered ? { opacity: 1, scale: 1, filter: 'blur(0px)' } : { opacity: 0, scale: 0.98, filter: 'blur(8px)' }}
        transition={{ duration: 0.8, ease: 'easeInOut' }}
      >
        {/* Animated Blobs/Graphics */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 0.15, scale: 1 }}
          transition={{ duration: 2 }}
          className="absolute -top-32 -left-32 w-[400px] h-[400px] bg-brand blur-3xl rounded-full z-0"
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 0.10, scale: 1 }}
          transition={{ duration: 2.2 }}
          className="absolute bottom-0 right-0 w-[350px] h-[350px] bg-brand-dark blur-2xl rounded-full z-0"
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.7 }}
          animate={{ opacity: 0.12, scale: 1 }}
          transition={{ duration: 2.5 }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-brand-light blur-2xl rounded-full z-0"
        />
        {/* Animated gradient background and floating blobs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
          className="absolute inset-0 z-0 rounded-2xl overflow-hidden"
        >
          <motion.div
            className="absolute -top-20 -left-24 w-[420px] h-[420px] bg-gradient-to-br from-gray-200 via-white to-gray-100 opacity-14 blur-[72px] rounded-full"
            animate={{ y: [0, 20, 0], x: [0, 10, 0] }}
            transition={{ duration: 10, repeat: Infinity, repeatType: 'reverse', ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute bottom-0 right-0 w-[320px] h-[320px] bg-gradient-to-tr from-gray-100 via-white to-brand-light opacity-10 blur-[88px] rounded-full"
            animate={{ y: [0, -12, 0], x: [0, -10, 0] }}
            transition={{ duration: 12, repeat: Infinity, repeatType: 'reverse', ease: 'easeInOut' }}
          />
        </motion.div>
        <motion.div
          className="relative z-10 w-full max-w-xl md:max-w-2xl p-6 bg-white bg-opacity-95 rounded-2xl shadow-xl hover:shadow-2xl transition-all max-h-[85vh] overflow-y-auto"
          initial={{ boxShadow: '0 2px 18px 0px #e5e7eb' }}
          whileHover={{ boxShadow: '0 4px 32px 0px #e5e7eb' }}
          transition={{ type: 'spring', stiffness: 120, damping: 18 }}
        >
          <div className="flex flex-col gap-3">
              {/* Resume */}
            <Section>
              <h3 className="text-lg font-semibold">Resume</h3>
              <div className="flex items-center gap-6">
                <FileUpload onFilesSelected={setResumeFiles} uploading={loading} progress={uploadProgress} />
                {resumeFiles.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-1">
                    {resumeFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center bg-gray-200 px-2 py-1 rounded">
                        <span className="text-sm text-gray-700">{file.name}</span>
                        <button type="button" className="ml-2 text-gray-500 hover:text-gray-700" onClick={() => setResumeFiles(prev => prev.filter((_, i) => i !== idx))}>
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                <DrivePicker label="Resume" onFilePicked={setResumeDriveFile} pickedFile={resumeDriveFile ?? undefined} disabled={loading} />
              </div>
              {resumeError && <span className="text-xs text-red-500">{resumeError}</span>}
            </Section>

            {/* <Section>
              <h3 className="text-lg font-semibold">Job Description</h3>
              <textarea
                placeholder="Paste job description here..."
                className="w-full h-24 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 resize-none"
                value={jobDescText}
                onChange={e => setJobDescText(e.target.value)}
                disabled={loading}
              />
              <div className="flex items-center gap-6">
                <FileUpload onFilesSelected={setJobDescFiles} uploading={loading} progress={uploadProgress} />
                <DrivePicker label="Pick from Drive" onFilePicked={setJobDescDriveFile} pickedFile={jobDescDriveFile ?? undefined} disabled={loading} />
                <input
                  type="url"
                  placeholder="Paste JD URL"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  value={jobDescUrl}
                  onChange={e => setJobDescUrl(e.target.value)}
                  disabled={loading}
                />
              </div>
              </Section> */}
              {/* Experience */}
            <Section>
              <h3 className="text-lg font-semibold">Experience</h3>
              <div className="flex items-center gap-6">
                <FileUpload onFilesSelected={setExpFiles} uploading={loading} progress={uploadProgress} />
                {expFiles.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-1">
                      {expFiles.map((file, idx) => (
                        <div key={idx} className="flex items-center bg-gray-200 px-2 py-1 rounded">
                          <span className="text-sm text-gray-700">{file.name}</span>
                          <button type="button" className="ml-2 text-gray-500 hover:text-gray-700" onClick={() => setExpFiles(prev => prev.filter((_, i) => i !== idx))}>
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                <DrivePicker label="Experience" onFilePicked={setExpDriveFile} pickedFile={expDriveFile ?? undefined} disabled={loading} />
              </div>
              {expError && <span className="text-xs text-red-500">{expError}</span>}
            </Section>
            {/* Project Readmes */}
            <Section>
              <h3 className="text-lg font-semibold">Project Readmes</h3>
              <div className="flex items-center gap-6">
                <FileUpload onFilesSelected={setReadmeFiles} uploading={loading} progress={uploadProgress} />
                    {readmeFiles.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-1">
                        {readmeFiles.map((file, idx) => (
                          <div key={idx} className="flex items-center bg-gray-200 px-2 py-1 rounded">
                            <span className="text-sm text-gray-700">{file.name}</span>
                            <button type="button" className="ml-2 text-gray-500 hover:text-gray-700" onClick={() => setReadmeFiles(prev => prev.filter((_, i) => i !== idx))}>
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                <DrivePicker label="Project Readme" onFilePicked={setReadmeDriveFile} pickedFile={readmeDriveFile ?? undefined} disabled={loading} />
              </div>
              {readmeError && <span className="text-xs text-red-500">{readmeError}</span>}
            </Section>

            {/* Job Description (moved below) */}
            <Section>
              <h3 className="text-lg font-semibold">Job Description</h3>
              <textarea
                placeholder="Paste job description here..."
                className="w-full h-24 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 resize-none"
                value={jobDescText}
                onChange={e => setJobDescText(e.target.value)}
                disabled={jobDescFiles.length > 0 || !!jobDescUrl}
              />
              <div className="flex items-center gap-6">
                <FileUpload onFilesSelected={files => { setJobDescFiles(files); setJobDescText(""); setJobDescUrl(""); }} uploading={loading} progress={uploadProgress} />
                <DrivePicker label="Pick from Drive" onFilePicked={setJobDescDriveFile} pickedFile={jobDescDriveFile ?? undefined} disabled={loading} />
                <input
                  type="url"
                  placeholder="Paste JD URL"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  value={jobDescUrl}
                  onChange={e => { setJobDescUrl(e.target.value); setJobDescText(""); setJobDescFiles([]); }}
                  disabled={loading || jobDescFiles.length > 0 || !!jobDescText}
                />
              </div>
              {jobDescError && <span className="text-xs text-red-500">{jobDescError}</span>}
            </Section>
            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              className="w-full py-3 bg-orange-500 text-white rounded-full font-semibold hover:bg-orange-600 transition disabled:opacity-50 flex items-center justify-center"
              disabled={loading}
            >
              {loading ? <Spinner /> : <span>Submit</span>}
            </button>
            {formError && <div className="text-center text-sm text-red-500 mt-2">{formError}</div>}

            {/* Output */}
            {outputFiles.length > 0 && (
              <Section>
                <h3 className="text-lg font-semibold">Results</h3>
                <OutputResult
                  files={outputFiles}
                  onEmail={async (email: string) => {
                    setEmailing(true);
                    setEmailError(null);
                    setEmailSuccess(false);
                    try {
                      // TODO: Replace with actual backend call
                      await new Promise(res => setTimeout(res, 1200));
                      setEmailSuccess(true);
                    } catch (e) {
                      setEmailError('Failed to send email.');
                    } finally {
                      setEmailing(false);
                    }
                  }}
                  emailing={emailing}
                  emailError={emailError}
                  emailSuccess={emailSuccess}
                />
              </Section>
            )}
            </div>
            {/* Animated Processing Overlay */}
            <AnimatePresence>
              {loading && (
                <motion.div
                  className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <motion.div
                    className="bg-white dark:bg-[#23232b] rounded-2xl shadow-2xl p-10 flex flex-col items-center"
                    initial={{ scale: 0.9, y: 40, opacity: 0 }}
                    animate={{ scale: 1, y: 0, opacity: 1 }}
                    exit={{ scale: 0.9, y: 40, opacity: 0 }}
                    transition={{ type: 'spring', stiffness: 200, damping: 22 }}
                  >
                    <Spinner />
                    <span className="mt-4 text-lg font-semibold text-brand">Processing your documents...</span>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
            {/* Output Result Display */}
            <OutputResult
              files={outputFiles}
              onEmail={async (email: string) => {
                setEmailing(true);
                setEmailError(null);
                setEmailSuccess(false);
                try {
                  // TODO: Replace with actual backend call
                  await new Promise(res => setTimeout(res, 1200));
                  setEmailSuccess(true);
                } catch (e) {
                  setEmailError('Failed to send email.');
                } finally {
                  setEmailing(false);
                }
              }}
              emailing={emailing}
              emailError={emailError}
              emailSuccess={emailSuccess}
            />
        </motion.div>
      </motion.section>
    </div>
  );
}