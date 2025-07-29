# **NLP Pipeline: A Structured Implementation Plan**

This document outlines the end-to-end structure for the NLP task at the core of your resume customization tool. The architecture is designed in distinct phases to ensure clarity, modularity, and maintainability.

### **Phase 1: Input Ingestion and Structured Parsing**

The goal of this phase is to receive all user inputs and convert them into a standardized, machine-readable format. The key is to be "structure-aware," especially for LaTeX documents.

**1\. Unified Input Collection:**

* Your FastAPI endpoint will accept a multipart form request containing:  
  * Resume file (.pdf, .tex)  
  * Job Description (text, file, or URL)  
  * Supporting documents (Experience PDFs, Project Readmes as .md or .pdf)

**2\. Comprehensive Context Aggregation:**

* Load the content from **all** supporting documents (job description, experience docs, projects) and concatenate them into a single, comprehensive text block. This will be the full\_context variable, serving as the complete source of truth for the AI's generation tasks.  
  * Use langchain\_community loaders (PyPDFLoader, UnstructuredMarkdownLoader, URL fetchers) for this.

**3\. Structure-Aware Resume Parsing (The Core Logic):**

* This is where the pipeline branches based on the resume file type.  
  * **Scenario A: LaTeX (.tex) Resume \- The "Preservation Path"**  
    * **Action:** Do NOT convert the .tex file to plain text immediately.  
    * **Tool:** Use a Python library like pylatexenc to parse the document into a node tree.  
    * **Process:**  
      1. Traverse the node tree to identify key structural commands (e.g., \\section{...}, \\subsection{...}).  
      2. Create a Python dictionary or a list of objects that maps each section (e.g., "Experience," "Education," "Skills") to its raw LaTeX content.  
      3. This creates a "structured representation" of the resume that maintains all original formatting. You now have both the full parsed document object and the isolated content of each section.  
  * **Scenario B: PDF (.pdf) Resume \- The "Reconstruction Path"**  
    * **Action:** Extract the full, clean text from the PDF.  
    * **Tool:** Use PyPDFLoader.  
    * **Process:** The output is a single string of unstructured text. The original visual structure is lost, so the goal shifts from "updating" to "rebuilding" the resume using a template.

### **Phase 2: AI-Powered Content Generation (Hierarchical Prompting)**

With parsed data and comprehensive context, this phase uses a two-tiered prompting strategy with LangChain and the Gemini API to generate highly tailored and consistent content.

**1\. Define the Core AI Persona and Rules (System Prompt):**

* This is a master "meta-prompt" that sets the global rules for the AI. It is sent with *every* request to establish the persona and constraints.  
  "You are an expert career coach and resume writer. Your goal is to help a candidate land their dream job by tailoring their application materials. Adhere to the following rules for all content you generate:  
  \- Use strong, professional language and active verbs.  
  \- Quantify achievements with metrics and data whenever possible (e.g., 'Increased efficiency by 20%' instead of 'Made things more efficient').  
  \- Ensure the tone is confident but not arrogant.  
  \- For resumes, focus on impact and results, not just responsibilities.  
  \- If you are working with LaTeX, you MUST preserve all original LaTeX commands and structure. Only modify the text content."

**2\. Create Focused Task-Specific Prompts:**

* These are shorter, more direct prompts that tell the AI what to do for a specific task. They work in conjunction with the System Prompt.  
  * **For a Specific Resume Section (e.g., "Experience"):**  
    "Following the core rules I've given you, your task is to rewrite the following resume section. Use the 'Full Context' provided to ensure the rewritten content is perfectly aligned with the target job.

    \*\*Full Context (Job Description, Projects, etc.):\*\*  
    {full\_context}

    \*\*Original Resume Section:\*\*  
    {original\_section\_content}

    \*\*Your Expertly Rewritten Section (preserving LaTeX):\*\*"

  * **For a Full Cover Letter:**  
    "Following the core rules I've given you, your task is to write a compelling cover letter. Use the candidate's information and the 'Full Context' to create a personalized, enthusiastic, and professional letter.

    \*\*Candidate's Full Resume Information:\*\*  
    {full\_resume\_text}

    \*\*Full Context (Job Description, Projects, etc.):\*\*  
    {full\_context}

    \*\*Your Professionally Written Cover Letter:\*\*"

**3\. Execute the LangChain Chain:**

* The LangChain execution will now combine the System Prompt with the Task-Specific Prompt for each call.  
* **For LaTeX Resumes:**  
  * Iterate through the "structured representation" from Phase 1\.  
  * For each relevant section, invoke the "Resume Section" chain, passing in that section's content and the full\_context.  
  * Store the AI-generated LaTeX content for each section.  
* **For PDF Resumes:**  
  * Invoke a single, broader chain that asks the AI to analyze the entire resume text against the full\_context and generate a complete, improved resume body.  
* **For the Cover Letter:**  
  * Invoke the "Cover Letter" chain separately, providing the full resume text and the full\_context.

### **Phase 3: Document Reconstruction and Finalization**

This phase takes the AI-generated content and assembles the final, polished documents.

**1\. Reconstruct the Document:**

* **For LaTeX Resumes (The "Preservation Path"):**  
  1. Go back to the parsed pylatexenc document object from Phase 1\.  
  2. Iterate through your AI-generated sections.  
  3. For each section, find its corresponding node in the document object and **replace its content** with the new, AI-generated LaTeX.  
  4. Serialize the modified document object back into a final .tex string.  
* **For PDF Resumes (The "Reconstruction Path"):**  
  1. Have a pre-defined, professional LaTeX template file stored in your backend (template.tex).  
  2. Inject the full, AI-generated resume body into this template. This creates the final .tex string.

**2\. Generate the Cover Letter File:**

* Take the raw string output from the cover letter chain and save it as a .txt file.

**3\. Compile to PDF:**

* **Tool:** Use **Tectonic**.  
* **Process:**  
  1. Run the Tectonic compiler on the final .tex files (both the updated original and the newly built one) to produce the final PDF resumes.  
  2. Optionally, use a tool like **WeasyPrint** to convert the .txt cover letter into a clean, professional-looking PDF.

**4\. Package for Delivery:**

* Assemble all generated files (.pdf, .tex, .txt) into a structured response that the frontend can easily handle for download or email delivery.