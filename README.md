# Study Plan Progress Tracker

A desktop application designed to help students track their study progress by extracting topics from PDF syllabi and providing an interactive checklist interface.

## Features

- **PDF syllabus parsing with intelligent topic detection**: Automatically extracts study topics from PDF syllabi, handling various formats.
- **Interactive checklist interface**: User-friendly checklist for tracking study progress with scrollable content.
- **Progress tracking and reporting**: Monitors and reports study progress, providing insights on topics completed.
- **Automatic progress saving and loading**: Progress is saved automatically, so students can continue from where they left off.
- **Support for various syllabus formats**:
  - Modular format (e.g., Module I, Module II, etc.)
  - Numbered sections
  - Bullet points
  - Roman numerals
  - Indented subtopics

## Requirements

To run the application, you will need:

- **Python 3.x**
- **PyPDF2**: A Python library for reading PDF files.
- **tkinter**: A standard Python library for creating graphical user interfaces (GUI).

## Installation

1. Clone or download the repository.
2. Install the required Python libraries:
    ```bash
    pip install PyPDF2
    ```
3. Run the application:
    ```bash
    python study_plan_tracker.py
    ```

## How to Use

1. **Load a Syllabus**: Open a PDF syllabus using the “Open Syllabus” button.
2. **Review Topics**: The topics will be extracted from the PDF and displayed as checkable items in the interactive checklist.
3. **Track Progress**: Check off topics as you complete them. The progress will be saved automatically.
4. **Review Progress**: The app provides a visual progress report, showing which topics have been completed.

## Contributing

Feel free to contribute to this project. If you have any ideas for improvement or bug fixes, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
