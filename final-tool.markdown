# Implementation Rules: Personalized Resume, CV, and Cover Letter Customization Tool

## 1. Overview
This document outlines the rules for implementing a production-ready Personalized Resume, CV, and Cover Letter Customization Tool. The application uses a **React** frontend and a **LangChain-powered backend** to automate the creation of tailored job application documents. It integrates with the **Google Gemini API** for NLP and **Tectonic** for LaTeX handling. The tool supports a wide range of input sources:

**Supported Inputs:**
- **Resume:** Upload as PDF or LaTeX (`.pdf`, `.tex`)
- **Job Description:** Paste text, upload a file, or provide a URL
- **Experience Document:** Upload as PDF
- **Project Readmes:** Upload as PDF or Markdown (`.pdf`, `.md`)
- **Google Drive Picker:** Optionally select any of the above files directly from the user's Google Drive

All input types are validated on the frontend and backend. The implementation focuses on a simplified, stateless architecture that is easy to develop, deploy, and maintain.

## 2. Project Setup and Initialization
### Objective
Establish a clean project environment, directory structure, and dependencies.

### Implementation Rules
- **Directory Structure**:
  - `frontend/`: Contains the React SPA (`src/`, `public/`, `package.json`).
  - `backend/`: Contains the LangChain application (`main.py`, `requirements.txt`, `.env`).
- **Dependencies**:
  - **Frontend**: `react`, `typescript`, `tailwindcss`, `axios`, `zustand`.
  - **Backend**: `python@3.11`, `langchain`, `langchain-google-genai`, `langchain_community` (for document loaders), `tectonic`, `weasyprint`, `python-dotenv`.
- **Environment Configuration**:
  - Create a `.env` file in the `backend/` directory with the following keys:
    - `GOOGLE_API_KEY`: Your Google Gemini API key.
    - `GMAIL_USER`: Your Gmail address for sending emails.
    - `GMAIL_PASSWORD`: Your Gmail App Password for SMTP.

### Testing Strategy
- **Validation**:
  - Ensure all dependencies are installed correctly using `npm install` and `pip install -r requirements.txt`.
  - Verify that the `.env` file is correctly loaded by the backend application.

## 3. Frontend Implementation
### Objective
Develop a responsive and intuitive React SPA for user interaction.

### Implementation Rules
- **Framework**: React 18 with TypeScript.
- **Styling**: Use Tailwind CSS for a utility-first styling approach.
- **Components**:
  - `FileUploadComponent`: Handles single or multiple file uploads, including support for Google Drive picker for all input types (resume, experience, readmes, job description).
  - `InputFormComponent`: Provides text areas for the job description (paste or URL), and manages selection/validation for all input types.
  - `OutputComponent`: Displays the generated documents and provides download/email options.
- **API Integration**: Use `axios` to send a `POST` request with all user inputs (files, text, URLs, Drive file IDs) to the backend API endpoint.
- **State Management**: Use `zustand` for simple, lightweight global state management.
- **Error Handling**: Display clear error messages to the user if the backend returns an error.

### Testing Strategy
- **Unit Tests**: Use Jest and React Testing Library to test individual components.
- **Integration Tests**: Test the full user flow, from uploading files to receiving the final output, by mocking the backend API response.

## 4. Backend Implementation
### Objective
Build a stateless LangChain application to handle all document processing and AI-powered content generation.

### Implementation Rules
- **Framework**: LangChain with Python 3.11.
- **Core Logic**: All processing is handled within a **LangChain Expression Language (LCEL)** chain.
- **API Layer**: Expose the LangChain application via a single API endpoint using a lightweight wrapper like Flask or FastAPI.
- **Stateless Design**: The application must not store any user data or session information. All processing is done in-memory per request.
- **File Handling**: Input files (from upload or Drive), pasted text, and URLs are received, validated, processed, and deleted from temporary storage within the same request cycle. The backend uses appropriate document loaders for each type: PDF, LaTeX, Markdown, plain text, and URL fetchers.

### Testing Strategy
- **Unit Tests**: Test individual components of the LangChain chain (prompts, parsers, LLM calls) in isolation.
- **Integration Tests**: Test the full chain with sample inputs, mocking the Gemini API to ensure the chain executes correctly.

## 5. NLP and LaTeX Handling
### Objective
Integrate the Google Gemini API for NLP tasks and Tectonic for reliable LaTeX compilation.

### Implementation Rules
- **NLP Tasks**: Define all NLP logic (e.g., text cleaning, content generation) within the LangChain chain using prompts and output parsers.
- **Prompt Management**: Store prompt templates in a dedicated `prompts/` directory and load them into the chain.
- **LaTeX Compilation**: If a user uploads a `.tex` file, preserve its structure. Inject the AI-generated content and compile the final document to PDF using **Tectonic**.
- **Error Handling**: Implement try-except blocks to catch errors during API calls or LaTeX compilation and return a meaningful error message to the user.

### Testing Strategy
- **Unit Tests**: Test prompt template rendering and Tectonic compilation with valid and invalid inputs.
- **Integration Tests**: Mock the Gemini API to test the full NLP and LaTeX generation flow.

## 6. Output and Delivery
### Objective
Generate and deliver the final documents to the user.

### Implementation Rules
- **Output Formats**: Generate resumes as `.tex` and `.pdf`, and cover letters as `.txt` and `.pdf`.
- **Delivery**: Provide options for direct download from the browser or delivery as email attachments using `smtplib`.
- **Security**: Validate recipient email addresses and ensure that only permitted file types are attached.

### Testing Strategy
- **Unit Tests**: Test the file generation for each format and the email sending logic with a mocked SMTP server.
- **Validation**: Ensure that downloaded files and email attachments are correct and not corrupted.

## 7. Deployment
### Objective
Deploy the frontend and backend applications.

### Implementation Rules
- **Frontend**: Deploy as a static site on **Vercel** or **Netlify**.
- **Backend**: Containerize the LangChain application using **Docker** and deploy it on a VPS or as a serverless function (e.g., AWS Lambda, Google Cloud Functions).

### Validation
-   Ensure the frontend can successfully communicate with the deployed backend API.
-   Confirm that environment variables are configured correctly in the production environment.