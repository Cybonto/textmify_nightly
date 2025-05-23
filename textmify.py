#!/usr/bin/env python3
import os
import sys
import argparse
import logging
import time
import re
from pathlib import Path
from typing import List, Optional
import traceback
from docling.document_converter import DocumentConverter, ConversionStatus, PdfFormatOption
from docling_core.types.doc import ImageRefMode
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
import tqdm
from colorama import init, Fore, Style
# Initialize colorama for cross-platform colored output
init()
# Handle SSL certificates (Zscaler)
try:
    import certifi
    # Path to your Zscaler certificate - update this to the correct path
    ZSCALER_CERT_PATH = "zscaler.crt"  # Update this path
    if os.path.exists(ZSCALER_CERT_PATH):
        os.environ['SSL_CERT_FILE'] = ZSCALER_CERT_PATH
        os.environ['REQUESTS_CA_BUNDLE'] = ZSCALER_CERT_PATH
        print(f"Using Zscaler certificate from {ZSCALER_CERT_PATH}")
    else:
        print(f"Warning: Zscaler certificate not found at {ZSCALER_CERT_PATH}")
        # Use default certifi certificates
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError as e:
    print(f"Warning: SSL certificate configuration failed: {str(e)}")
    print("SSL certificate verification might fail.")
# Configure logging with colors
def setup_logging(verbose: bool = False) -> logging.Logger:
    log_level = logging.DEBUG if verbose else logging.INFO
    class ColoredFormatter(logging.Formatter):
        FORMATS = {
            logging.DEBUG: Fore.CYAN + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
            logging.INFO: Fore.GREEN + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
            logging.WARNING: Fore.YELLOW + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
            logging.ERROR: Fore.RED + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
            logging.CRITICAL: Fore.RED + Style.BRIGHT + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL
        }
        def format(self, record):
            log_format = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
            return formatter.format(record)
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    logger = logging.getLogger('docling_translator')
    logger.setLevel(log_level)
    # Remove any existing handlers
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger
# Function to count words in a file
def count_words(file_path: Path) -> int:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            return len(re.findall(r'\b\w+\b', content))
    except Exception as e:
        logging.error(f"Error counting words in {file_path}: {str(e)}")
        return 0
# Function to detect supported file types based on Docling's capabilities
def is_supported_file(file_path: Path) -> bool:
    # Based on Docling's supported formats in the documentation
    supported_extensions = [
        '.pdf', '.docx', '.xlsx', '.pptx', '.md', '.asciidoc',
        '.html', '.xhtml', '.htm', '.csv', '.png', '.jpg', '.jpeg',
        '.tiff', '.bmp', '.xml', '.json'
    ]
    return file_path.suffix.lower() in supported_extensions
# Function to translate a file to markdown with retries using Docling
def translate_to_markdown(
    file_path: Path,
    output_dir: Path,
    logger: logging.Logger,
    pipeline_options: Optional[PdfPipelineOptions] = None,
    max_retries: int = 3,
    retry_delay: int = 2
) -> Optional[Path]:
    if not is_supported_file(file_path):
        logger.warning(f"Skipping unsupported file type: {file_path}")
        return None
    output_file = output_dir / f"{file_path.stem}.md"
    retries = 0
    while retries < max_retries:
        try:
            logger.debug(f"Converting {file_path} to markdown...")
            # Create DocumentConverter with specific options if provided
            if pipeline_options and file_path.suffix.lower() == '.pdf':
                converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
            else:
                converter = DocumentConverter()
            # Convert the document using Docling
            result = converter.convert(str(file_path))
            if result.status == ConversionStatus.SUCCESS:
                # Export the document to markdown and save it
                markdown_content = result.document.export_to_markdown(
                    image_mode=ImageRefMode.PLACEHOLDER
                )
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.debug(f"Successfully converted {file_path} to {output_file}")
                return output_file
            elif result.status == ConversionStatus.PARTIAL_SUCCESS:
                logger.warning(f"Partial success converting {file_path}. Some content may be missing.")
                # Still try to save what we got
                markdown_content = result.document.export_to_markdown(
                    image_mode=ImageRefMode.PLACEHOLDER
                )
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                return output_file
            else:
                logger.warning(f"Failed to convert {file_path} (attempt {retries+1}/{max_retries})")
                retries += 1
        except Exception as e:
            logger.warning(f"Error converting {file_path} (attempt {retries+1}/{max_retries}): {str(e)}")
            retries += 1
        if retries < max_retries:
            logger.debug(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
    logger.error(f"Failed to convert {file_path} after {max_retries} attempts")
    return None
# Function to combine markdown files
def combine_markdown_files(markdown_dir: Path, max_words: int = 100000,
                           logger: logging.Logger = None) -> List[Path]:
    markdown_files = list(markdown_dir.glob('*.md'))
    # Don't include already packed files
    markdown_files = [f for f in markdown_files if not f.stem.startswith('packed_')]
    if not markdown_files:
        if logger:
            logger.warning(f"No markdown files found in {markdown_dir}")
        return []
    combined_files = []
    current_file_index = 0
    current_word_count = 0
    current_content = []
    # Sort files to ensure consistent combining
    markdown_files.sort()
    for md_file in tqdm.tqdm(markdown_files, desc="Combining files", unit="file"):
        word_count = count_words(md_file)
        # If adding this file would exceed the word limit, save the current combined file
        # and start a new one (unless this is the first file)
        if current_word_count > 0 and current_word_count + word_count > max_words:
            output_path = markdown_dir / f"packed_{current_file_index}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n\n---\n\n'.join(current_content))
            combined_files.append(output_path)
            current_file_index += 1
            current_word_count = 0
            current_content = []
        # Add the current file to the combined content
        try:
            with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
                file_content = f.read()
                current_content.append(f"## {md_file.stem}\n\n{file_content}")
                current_word_count += word_count
        except Exception as e:
            if logger:
                logger.error(f"Error reading {md_file}: {str(e)}")
    # Save the last combined file if there's any content
    if current_content:
        output_path = markdown_dir / f"packed_{current_file_index}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n---\n\n'.join(current_content))
        combined_files.append(output_path)
    return combined_files
def main():
    parser = argparse.ArgumentParser(description='Convert files to markdown using Docling')
    parser.add_argument('folder', help='Folder containing files to convert')
    parser.add_argument('--combine', action='store_true',
                        help='Combine markdown files into packed files with max 100,000 words each')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--max-words', type=int, default=100000,
                        help='Maximum words per combined file (default: 100,000)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Custom output directory (default: "markdowns" subfolder)')
    parser.add_argument('--retries', type=int, default=3,
                        help='Number of retries for failed conversions (default: 3)')
    parser.add_argument('--no-ocr', action='store_true',
                        help='Disable OCR for PDF files (faster conversion)')
    parser.add_argument('--artifacts-path', type=str, default=os.path.expanduser("~/.cache/docling/models"),
                        help='Path to model artifacts directory (default: ~/.cache/docling/models)')
    args = parser.parse_args()
    logger = setup_logging(args.verbose)
    logger.info("Logger initialized")
    
    # Use the models path
    if args.artifacts_path:
        if os.path.exists(args.artifacts_path):
            logger.info(f"Using model artifacts from: {args.artifacts_path}")
        else:
            logger.warning(f"Specified artifacts path does not exist: {args.artifacts_path}")
            logger.warning("Run 'docling-tools models download' to download the models first")
    
    # Ensure the folder exists
    input_folder = Path(args.folder)
    if not input_folder.exists() or not input_folder.is_dir():
        logger.error(f"Folder '{args.folder}' does not exist or is not a directory")
        sys.exit(1)
    # Create output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_folder / "markdowns"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    # Get all files in the folder (exclude hidden files and directories)
    all_files = [f for f in input_folder.glob('*')
                if f.is_file() and not f.name.startswith('.')]
    # Filter for supported file types
    supported_files = [f for f in all_files if is_supported_file(f)]
    if not supported_files:
        logger.warning(f"No supported files found in {args.folder}")
        logger.info("Supported formats: PDF, DOCX, XLSX, PPTX, MD, AsciiDoc, HTML, XHTML, CSV, PNG, JPEG, TIFF, BMP, XML, JSON")
        sys.exit(0)
    # Set up pipeline options based on command line arguments
    pipeline_options = PdfPipelineOptions()
    if args.no_ocr:
        pipeline_options.do_ocr = False
    if args.artifacts_path:
        pipeline_options.artifacts_path = args.artifacts_path
    # Process each file
    successful_files = []
    logger.info(f"Found {len(supported_files)} supported files to process out of {len(all_files)} total files")
    # Create progress bar
    for file_path in tqdm.tqdm(supported_files, desc="Converting files", unit="file"):
        logger.info(f"Processing file {file_path}")
        result_path = translate_to_markdown(
            file_path,
            output_dir,
            logger,
            pipeline_options=pipeline_options,
            max_retries=args.retries
        )
        if result_path:
            successful_files.append(result_path)
            logger.info(f"Successfully processed {file_path}")
        else:
            logger.error(f"Failed to process {file_path}")
    logger.info(f"Successfully converted {len(successful_files)} out of {len(supported_files)} files")
    # Combine markdown files if requested
    if args.combine and successful_files:
        logger.info(f"Combining markdown files (max {args.max_words} words per file)...")
        combined_files = combine_markdown_files(output_dir, max_words=args.max_words, logger=logger)
        if combined_files:
            logger.info(f"Created {len(combined_files)} combined files:")
            for cf in combined_files:
                word_count = count_words(cf)
                logger.info(f"  - {cf.name} ({word_count} words)")
        else:
            logger.warning("No combined files were created")
    # Print summary
    print("\n" + "="*60)
    print(f"{Fore.GREEN}Conversion Summary:{Style.RESET_ALL}")
    print(f"  - Input folder: {input_folder}")
    print(f"  - Output folder: {output_dir}")
    print(f"  - Files processed: {len(supported_files)}")
    print(f"  - Files successfully converted: {len(successful_files)}")
    if args.combine and successful_files:
        print(f"  - Combined files created: {len(combined_files)}")
    print("="*60)
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Process interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
        sys.exit(1)