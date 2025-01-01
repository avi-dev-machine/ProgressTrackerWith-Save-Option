import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import PyPDF2
import re
import logging
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('study_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PDFTopicExtractor:
    """Handles PDF parsing and topic extraction."""
    
    SUBJECT_PATTERNS = [
        r'^Module\s+[IVX]+:?\s*\[\d+L\]',  # Matches "Module I: [10L]"
        r'^Module\s+\d+:?\s*\[\d+L\]',      # Matches "Module 1: [10L]"
        r'^[A-Z][A-Za-z\s\-]+:',            # Matches main topic headings with colon
        r'^[IVX]+\.',                        # Matches Roman numeral sections
        r'^\d+\.\s*[A-Z]'                   # Matches numbered sections
    ]
    
    SUBTOPIC_PATTERNS = [
        r'^\s*[-•●※*]\s',                   # Bullet points
        r'^\s*[a-z]\)\s',                   # Matches a) b) c) style
        r'^\s*\d+\.\d*\s',                  # Numbered items
        r'^\s{2,}[A-Z][^:]+:',             # Indented topics with colon
        r'^\s{2,}[A-Z]',                   # Indented capitalized lines
        r'(?<=:)([^,.]+)(?=[,.])'          # Captures items between colons and commas/periods
    ]
    
    @staticmethod
    def extract_topics_from_pdf(pdf_path: str) -> Dict[str, List[str]]:
        """
        Extract topics and subtopics from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with topics as keys and lists of subtopics as values
        """
        try:
            topics: Dict[str, List[str]] = {}
            current_subject: Optional[str] = None
            
            logger.debug(f"Opening PDF file: {pdf_path}")
            with open(pdf_path, 'rb') as file:
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    logger.debug(f"Number of pages: {len(pdf_reader.pages)}")
                    
                    text = ''
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            page_text = page.extract_text()
                            logger.debug(f"\n--- Raw text from page {page_num + 1} ---\n{page_text}\n-------------------")
                            text += page_text
                        except Exception as e:
                            logger.error(f"Error extracting text from page {page_num + 1}: {str(e)}")
                    
                    lines = text.split('\n')
                    for line in lines:
                        clean_line = line.strip()
                        
                        if not clean_line:
                            continue
                        
                        # Check if line matches any subject pattern
                        is_subject = any(re.match(pattern, clean_line) for pattern in PDFTopicExtractor.SUBJECT_PATTERNS)
                        if is_subject:
                            current_subject = clean_line
                            topics[current_subject] = []
                            logger.debug(f"Found subject: {current_subject}")
                            continue
                        
                        # Check if line matches any subtopic pattern
                        is_subtopic = any(re.match(pattern, line) for pattern in PDFTopicExtractor.SUBTOPIC_PATTERNS)
                        if current_subject is not None and (is_subtopic or '  ' in line):
                            subtopic = re.sub(r'^\s*[-•●※*\d.]\s*', '', clean_line)
                            if subtopic and len(subtopic.strip()) > 0:
                                topics[current_subject].append(subtopic.strip())
                                logger.debug(f"Added subtopic to {current_subject}: {subtopic}")
                    
                    # Remove empty subjects and try alternative parsing if needed
                    topics = PDFTopicExtractor._clean_and_validate_topics(topics, lines)
                    return topics
                    
                except Exception as e:
                    logger.error(f"Error reading PDF: {str(e)}")
                    messagebox.showerror("Error", f"Failed to read PDF: {str(e)}")
                    return {"Error": ["Failed to read PDF"]}
                    
        except Exception as e:
            logger.error(f"Error opening file: {str(e)}")
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            return {"Error": ["Failed to open file"]}
    
    @staticmethod
    def _clean_and_validate_topics(topics: Dict[str, List[str]], lines: List[str]) -> Dict[str, List[str]]:
        """Clean up and validate extracted topics, attempting alternative parsing if needed."""
        # Remove empty subjects
        topics = {k: v for k, v in topics.items() if v}
        
        # If no topics found, try alternative parsing
        if not topics:
            logger.debug("No topics found with primary patterns, trying alternative parsing...")
            current_subject = None
            for line in lines:
                clean_line = line.strip()
                if not clean_line:
                    continue
                
                if (len(clean_line) > 3 and (
                    clean_line.isupper() or 
                    clean_line.endswith(':') or
                    re.match(r'^\d+\.?\s+[A-Z]', clean_line))):
                    current_subject = clean_line
                    topics[current_subject] = []
                elif current_subject and clean_line:
                    topics[current_subject].append(clean_line)
        
        # If still no topics found, create a default section
        if not topics:
            logger.warning("No topics found in PDF")
            messagebox.showwarning(
                "Warning",
                "Could not detect topics in the PDF. The file might be scanned or in a format that's hard to parse. "
                "Try a different PDF or check the file format."
            )
            topics["Detected Content"] = [line.strip() for line in lines if line.strip()][:10]
        
        return topics

class StudyTracker:
    """Main application class for the Study Plan Progress Tracker."""
    
    def __init__(self):
        """Initialize the application and set up the UI."""
        self.app = tk.Tk()
        self.app.title("Study Plan Progress Tracker")
        self.app.geometry("800x600")
        
        self._setup_ui()
        self.topics: Dict[str, List[str]] = {}
        self.checkbox_vars: Dict[str, tk.BooleanVar] = {}
        
    def _setup_ui(self):
        """Set up the user interface components."""
        # Main frame with scrollbar
        self.main_frame = tk.Frame(self.app)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar setup
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar components
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Buttons frame
        self.buttons_frame = tk.Frame(self.app)
        self.buttons_frame.pack(pady=10)
        
        # Add buttons
        self._create_buttons()
        
        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _create_buttons(self):
        """Create and configure the application buttons."""
        buttons = [
            ("Load PDF", self.load_pdf),
            ("Check Progress", self.check_progress),
            ("Save Progress", self.save_progress)
        ]
        
        for text, command in buttons:
            tk.Button(self.buttons_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def load_pdf(self):
        """Load and process a PDF file."""
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if pdf_path:
            logger.debug(f"Selected PDF file: {pdf_path}")
            self.topics = PDFTopicExtractor.extract_topics_from_pdf(pdf_path)
            if self.topics:
                logger.debug(f"Extracted topics: {list(self.topics.keys())}")
                self.refresh_ui()
            else:
                logger.error("No topics extracted from PDF")
                messagebox.showerror("Error", "No topics could be extracted from the PDF")
    
    def refresh_ui(self):
        """Refresh the UI with current topics and load saved progress."""
        # Clear existing UI
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        logger.debug("Refreshing UI with topics")
        # Create frames for each subject
        for subject, items in self.topics.items():
            self._create_subject_frame(subject, items)
        
        self.load_progress()
    
    def _create_subject_frame(self, subject: str, items: List[str]):
        """Create a frame for a subject and its subtopics."""
        frame = tk.LabelFrame(self.scrollable_frame, text=subject, padx=10, pady=10)
        frame.pack(padx=10, pady=5, fill="x", expand=True)
        
        for item in items:
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(frame, text=item, variable=var, wraplength=600)
            checkbox.pack(anchor="w")
            self.checkbox_vars[item] = var
    
    def save_progress(self):
        """Save current progress to a JSON file."""
        try:
            progress = {key: var.get() for key, var in self.checkbox_vars.items()}
            with open('progress.json', 'w') as f:
                json.dump(progress, f)
            logger.debug("Progress saved successfully")
            messagebox.showinfo("Success", "Progress saved successfully!")
        except Exception as e:
            logger.error(f"Error saving progress: {str(e)}")
            messagebox.showerror("Error", f"Failed to save progress: {str(e)}")
    
    def load_progress(self):
        """Load saved progress from JSON file."""
        try:
            if os.path.exists('progress.json'):
                with open('progress.json', 'r') as f:
                    progress = json.load(f)
                    for topic, is_completed in progress.items():
                        if topic in self.checkbox_vars:
                            self.checkbox_vars[topic].set(is_completed)
                logger.debug("Progress loaded successfully")
        except Exception as e:
            logger.error(f"Error loading progress: {str(e)}")
            messagebox.showerror("Error", f"Failed to load progress: {str(e)}")
    
    def check_progress(self):
        """Generate and display a progress report."""
        completed = [key for key, var in self.checkbox_vars.items() if var.get()]
        incomplete = [key for key, var in self.checkbox_vars.items() if not var.get()]
        
        total = len(completed) + len(incomplete)
        if total > 0:
            completion_rate = (len(completed) / total) * 100
            message = (
                f"Progress: {completion_rate:.1f}%\n\n"
                f"Completed Topics ({len(completed)}):\n"
                + "\n".join(f"• {topic}" for topic in completed)
                + f"\n\nIncomplete Topics ({len(incomplete)}):\n"
                + "\n".join(f"• {topic}" for topic in incomplete)
            )
        else:
            message = "No topics available. Please load a PDF first."
        
        messagebox.showinfo("Progress Report", message)
        self.save_progress()
    
    def run(self):
        """Start the application."""
        self.app.mainloop()

if __name__ == "__main__":
    app = StudyTracker()
    app.run()
