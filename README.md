# Textmify

A tool to translate various document formats to Markdown using IBM Docling, with options to combine the resulting markdown files.

## Features

- Translates various document formats to Markdown (PDF, DOCX, XLSX, PPTX, HTML, images, and more)
- Combines multiple markdown files into larger documents with customizable word limits
- Cross-platform support (Windows, macOS, Linux)
- Robust error handling and retry mechanism
- Progress tracking with status bars
- Detailed logging with color-coded output
- Runs in a virtual environment to prevent dependency conflicts
- Offline capability with pre-downloaded models

## Installation

### Prerequisites

- Python 3.6 or higher
- Internet connection for downloading dependencies and models

### Installation Steps

#### For Windows:

1. Download or clone this repository
2. Open a command prompt and navigate to the repository directory
3. Run the installer:
   ```
   install.bat
   ```

#### For macOS/Linux:

1. Download or clone this repository
2. Open a terminal and navigate to the repository directory
3. Make the installer executable:
   ```
   chmod +x install.sh
   ```
4. Run the installer:
   ```
   sh ./install.sh
   ```

The installer will:
- Create a virtual environment
- Install required dependencies
- Configure SSL certificates if needed
- Pre-download the necessary Docling models

## Usage

### Activating the Virtual Environment

Before using the tool, activate the virtual environment:
- **Windows**:
  ```
  venv\Scripts\activate
  ```
- **macOS/Linux**:
  ```
  source venv/bin/activate
  ```

### Basic Usage

To translate all supported files in a folder to Markdown:
```
python textmify.py /path/to/your/folder
```
This will create a `markdowns` folder inside your specified directory with all translated files.

### Combining Markdown Files

To translate files and combine them into larger markdown files (with a maximum word limit):
```
python textmify.py /path/to/your/folder --combine
```

### Advanced Options

```
python textmify.py [FOLDER] [OPTIONS]
Options:
  --combine           Combine markdown files into packed files
  --verbose           Enable detailed logging
  --max-words N       Maximum words per combined file (default: 100000)
  --output-dir DIR    Custom output directory
  --retries N         Number of retries for failed translations (default: 3)
  --no-ocr            Disable OCR for PDF files (faster conversion)
  --artifacts-path    Path to model artifacts directory (default: ~/.cache/docling/models)
```

## Supported File Types

- PDF (.pdf)
- Microsoft Office (.docx, .xlsx, .pptx)
- Markdown (.md)
- AsciiDoc (.asciidoc)
- HTML (.html, .xhtml, .htm)
- CSV (.csv)
- Images (.png, .jpg, .jpeg, .tiff, .bmp)
- Structured data (.xml, .json)

## Examples

### Basic Translation

```
python textmify.py ~/Documents/my_files
```

### Combine with Custom Word Limit

```
python textmify.py ~/Documents/my_files --combine --max-words 50000
```

### Specify Custom Output Directory

```
python textmify.py ~/Documents/my_files --output-dir ~/Documents/markdown_output
```

### Disable OCR for Faster Processing

```
python textmify.py ~/Documents/my_files --no-ocr
```

### Use Custom Model Path

```
python textmify.py ~/Documents/my_files --artifacts-path /path/to/models
```

### Enable Verbose Logging

```
python textmify.py ~/Documents/my_files --verbose
```


## Troubleshooting

### Common Issues

1. **SSL certificate errors**:
   - Run `docling-tools models download` to pre-download models
   - Check that your corporate certificates are properly installed

2. **Missing dependencies**:
   - Ensure you've activated the virtual environment
   - Try running the installation script again

3. **Unsupported file types**:
   - Check the list of supported file types above
   - Consider converting your files to a supported format

4. **Translation failures**:
   - Use the `--verbose` flag to see detailed error messages
   - Try increasing the number of retries with `--retries N`
   - For large PDFs, try with `--no-ocr` flag for faster processing

### Reporting Issues

If you encounter problems not covered here, please open an issue on the GitHub repository with:
1. The exact command you ran
2. The error message you received
3. Your operating system and Python version (`python --version`)

## License

This project is licensed under the CC License - see the LICENSE file for details.

## Acknowledgments

- IBM Docling for the document translation functionality
- tqdm for the progress bars
- colorama for color-coded terminal output

