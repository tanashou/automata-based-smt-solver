"""File discovery utilities for benchmark processing."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def discover_smt2_files(directory: Path, pattern: str = "*.smt2") -> list[Path]:  # noqa: C901, PLR0912, PLR0915
    """Discover all SMT2 files in the specified directory.

    Args:
        directory: Path to the directory to search
        pattern: Glob pattern for file matching (default: "*.smt2")

    Returns:
        List of Path objects for discovered files

    Raises:
        FileNotFoundError: If the directory doesn't exist
        PermissionError: If the directory cannot be accessed
        NotADirectoryError: If the path is not a directory

    """
    logger.info("Starting file discovery in directory: %s", directory)
    logger.info("Using pattern: %s", pattern)

    try:
        # Check if directory exists with enhanced error context
        if not directory.exists():
            error_msg = f"Benchmark directory does not exist: {directory}"
            logger.error(error_msg)
            logger.error("Possible causes:")
            logger.error("  - Incorrect directory path specified")
            logger.error("  - Directory was moved or deleted")
            logger.error("  - Network path is unavailable")
            raise FileNotFoundError(error_msg)  # noqa: TRY301

        # Check if path is actually a directory with enhanced error context
        if not directory.is_dir():
            error_msg = f"Path exists but is not a directory: {directory}"
            logger.error(error_msg)
            logger.error("Possible causes:")
            logger.error("  - Path points to a regular file instead of directory")
            logger.error("  - Path points to a symbolic link to a file")
            logger.error("  - Path points to a special file (device, socket, etc.)")
            raise NotADirectoryError(error_msg)  # noqa: TRY301

        # Attempt to list directory contents to check permissions
        try:
            directory_contents = list(directory.iterdir())
            logger.debug("Directory contains %d items", len(directory_contents))
        except PermissionError as e:
            error_msg = f"Permission denied: Cannot access directory {directory}"
            logger.exception(error_msg)
            logger.exception("Possible solutions:")
            logger.exception("  - Check file system permissions for the directory")
            logger.exception("  - Run with appropriate user privileges")
            logger.exception(
                "  - Verify directory is not restricted by system policies"
            )
            raise PermissionError(error_msg) from e
        except OSError as e:
            error_msg = f"OS error while accessing directory {directory}: {e}"
            logger.exception(error_msg)
            logger.exception("Possible causes:")
            logger.exception("  - Network connectivity issues")
            logger.exception("  - File system corruption")
            logger.exception("  - Resource exhaustion (too many open files)")
            raise OSError(error_msg) from e

        # Use glob to find all matching files with enhanced error handling
        logger.debug(
            "Searching for files matching pattern '%s' in %s", pattern, directory
        )
        try:
            files = list(directory.glob(pattern))
            logger.debug("Pattern matching found %d potential matches", len(files))
        except OSError as e:
            error_msg = f"Error during file pattern matching in {directory}: {e}"
            logger.exception(error_msg)
            logger.exception("Possible causes:")
            logger.exception("  - Invalid glob pattern syntax")
            logger.exception("  - File system access issues during pattern matching")
            logger.exception("  - Resource limitations during directory traversal")
            raise OSError(error_msg) from e
        except ValueError as e:
            error_msg = f"Invalid pattern '{pattern}' for file matching: {e}"
            logger.exception(error_msg)
            logger.exception("Please check that the pattern uses valid glob syntax")
            raise ValueError(error_msg) from e

        # Filter to ensure we only get files with enhanced error handling
        smt2_files = []
        files_skipped = 0
        for f in files:
            try:
                if f.is_file():
                    smt2_files.append(f)
                    logger.debug("Added file: %s", f.name)
                else:
                    logger.debug("Skipping non-file: %s", f)
                    files_skipped += 1
            except OSError as e:
                logger.warning("Cannot check if %s is a file, skipping: %s", f, e)
                logger.warning(
                    "This could indicate file system issues or permission problems"
                )
                files_skipped += 1
                continue
            except Exception:
                logger.exception("Unexpected error checking file %s", f)
                files_skipped += 1
                continue

        if files_skipped > 0:
            logger.info(
                "Skipped %d items that could not be processed as files",
                files_skipped,
            )

        # Sort files for consistent ordering
        try:
            smt2_files.sort()
            logger.debug("Files sorted successfully for consistent processing order")
        except Exception:  # noqa: BLE001
            logger.warning("Could not sort file list")
            logger.warning("Processing will continue with unsorted file list")

        logger.info(
            "File discovery completed: %d SMT2 files found in %s",
            len(smt2_files),
            directory,
        )
        # Also log a concise completion message (used by tests)
        concise_msg = (
            "File discovery completed: " + str(len(smt2_files)) + " SMT2 files found"
        )
        logger.info(concise_msg)

        # Handle empty directory case gracefully with enhanced guidance
        if not smt2_files:
            warning_msg = (
                f"No files matching pattern '{pattern}' found in directory {directory}"
            )
            logger.warning(warning_msg)
            logger.info("Diagnostic information:")
            logger.info("  - Directory exists: %s", directory.exists())
            logger.info("  - Directory is accessible: True")
            logger.info("  - Total items in directory: %d", len(directory_contents))
            logger.info("  - Pattern used: %s", pattern)
            logger.info("Possible causes:")
            logger.info("  - Empty directory")
            logger.info("  - No files matching the specified pattern")
            logger.info("  - Files with different extensions or naming conventions")
            logger.info("  - All matching items are directories, not files")

            # Provide helpful suggestions based on directory contents
            if directory_contents:
                sample_items = [item.name for item in directory_contents[:5]]
                logger.info("  - Sample directory contents: %s", sample_items)

                # Check for common file extensions
                extensions = set()
                for item in directory_contents:
                    if item.is_file() and "." in item.name:
                        extensions.add(item.suffix.lower())

                if extensions:
                    logger.info(
                        "  - File extensions found: %s",
                        sorted(extensions),
                    )
                    if ".smt2" not in extensions and pattern == "*.smt2":
                        logger.info(
                            "  - Consider using a different pattern or "
                            "checking file extensions"
                        )

        return smt2_files  # noqa: TRY300

    except FileNotFoundError:
        # Re-raise with additional context already provided
        raise
    except NotADirectoryError:
        # Re-raise with additional context already provided
        raise
    except PermissionError:
        # Re-raise with additional context already provided
        raise
    except ValueError:
        # Re-raise with additional context already provided
        raise
    except OSError as e:
        error_msg = f"Unexpected OS error during file discovery in {directory}: {e}"
        logger.exception(error_msg)
        logger.exception(
            "This indicates a system-level issue that prevented file discovery"
        )
        raise OSError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error during file discovery in {directory}: {e}"
        logger.exception(error_msg)
        logger.exception(
            "This indicates an internal error in the file discovery process"
        )
        logger.exception("Please report this issue with the full error details")
        raise RuntimeError(error_msg) from e


def validate_file(file_path: Path) -> bool:  # noqa: C901, PLR0911, PLR0912, PLR0915
    """Validate that a file exists and is readable.

    Args:
        file_path: Path to the file to validate

    Returns:
        True if file is valid and readable, False otherwise

    """
    logger.debug("Validating file: %s", file_path)

    try:
        # Check if file exists with enhanced error context
        if not file_path.exists():
            logger.warning(
                "File validation failed - file does not exist: %s",
                file_path,
            )
            logger.debug("Possible causes:")
            logger.debug("  - File was deleted after discovery")
            logger.debug("  - File path contains invalid characters")
            logger.debug("  - Network connectivity issues for remote files")
            return False

        # Check if path is actually a file with enhanced error context
        if not file_path.is_file():
            logger.warning(
                "File validation failed - path is not a regular file: %s",
                file_path,
            )
            try:
                if file_path.is_dir():
                    logger.debug("Path is a directory: %s", file_path)
                elif file_path.is_symlink():
                    logger.debug("Path is a symbolic link: %s", file_path)
                    # Check if symlink target exists
                    try:
                        target = file_path.resolve()
                        logger.debug("Symlink target: %s", target)
                        if not target.exists():
                            logger.debug(
                                "Symlink target does not exist (broken symlink)"
                            )
                    except OSError as symlink_e:
                        logger.debug("Cannot resolve symlink: %s", symlink_e)
                else:
                    logger.debug("Path is a special file type: %s", file_path)
            except OSError as type_check_e:
                logger.debug("Cannot determine file type: %s", type_check_e)
            return False

        # Check file size and provide detailed information
        try:
            file_stats = file_path.stat()
            file_size = file_stats.st_size
            logger.debug("File size: %d bytes", file_size)

            if file_size == 0:
                logger.warning(
                    "File validation warning - file is empty: %s",
                    file_path,
                )
                logger.debug("Empty files may cause issues with SMT solvers")
                # Don't return False for empty files, let the solver handle it
            elif file_size > 100 * 1024 * 1024:  # 100MB
                logger.info(
                    "Large file detected (%.1f MB): %s",
                    file_size / (1024 * 1024),
                    file_path,
                )
                logger.debug("Large files may require more processing time and memory")

        except OSError:
            logger.exception(
                "File validation failed - cannot get file stats for %s",
                file_path,
            )
            logger.exception("Possible causes:")
            logger.exception("  - File system corruption")
            logger.exception("  - Permission issues")
            logger.exception("  - Network connectivity problems")
            return False
        except Exception:
            logger.exception(
                "File validation failed - unexpected error getting file stats for %s",
                file_path,
            )
            return False

        # Try to read the file to check if it's accessible with enhanced error handling
        try:
            with file_path.open("r", encoding="utf-8") as f:
                # Read first few characters to verify readability
                try:
                    content = f.read(10)
                    logger.debug(
                        "Successfully read %d characters from file",
                        len(content),
                    )

                    if not content and file_size > 0:
                        logger.warning(
                            "File validation warning - file appears to have "
                            "content but read returned empty: %s",
                            file_path,
                        )
                        logger.debug(
                            "This could indicate binary content or encoding issues"
                        )

                except OSError:
                    logger.exception(
                        "File validation failed - I/O error reading file %s",
                        file_path,
                    )
                    logger.exception("Possible causes:")
                    logger.exception("  - File is locked by another process")
                    logger.exception("  - Hardware issues with storage device")
                    logger.exception("  - Network interruption for remote files")
                    return False

        except PermissionError:
            logger.exception(
                "File validation failed - permission denied reading file %s",
                file_path,
            )
            logger.exception("Possible solutions:")
            logger.exception("  - Check file permissions")
            logger.exception("  - Run with appropriate user privileges")
            logger.exception("  - Verify file is not exclusively locked")
            return False

        except UnicodeDecodeError as e:
            logger.warning(
                "File validation warning - UTF-8 encoding issue for %s: %s",
                file_path,
                e,
            )
            logger.debug(
                "Encoding error at position %d-%d: %s",
                e.start,
                e.end,
                e.reason,
            )

            # Try with different encoding as fallback
            try:
                with file_path.open("r", encoding="latin-1") as f:
                    fallback_content = f.read(10)
                    logger.info(
                        "File %s readable with latin-1 encoding",
                        file_path.name,
                    )
                    logger.debug(
                        "Read %d characters with fallback encoding",
                        len(fallback_content),
                    )

            except OSError:
                logger.exception(
                    "File validation failed - cannot read file %s with any encoding",
                    file_path,
                )
                logger.exception(
                    "File may be binary or use an unsupported text encoding"
                )
                return False

            # SMT2 files should be text files,
            # consider it valid if readable with fallback encoding
            logger.debug("File accepted with fallback encoding")
            return True

        except FileNotFoundError:
            logger.exception(
                "File validation failed - file disappeared during validation: %s",
                file_path,
            )
            logger.debug(
                "File may have been deleted by another process during validation"
            )
            return False

        except OSError:
            logger.exception(
                "File validation failed - OS error reading file %s",
                file_path,
            )
            logger.exception("Possible causes:")
            logger.exception("  - File system errors")
            logger.exception("  - Resource exhaustion")
            logger.exception("  - Hardware issues")
            return False

        except Exception:
            logger.exception(
                "File validation failed - unexpected error reading file %s",
                file_path,
            )
            logger.exception("This indicates an internal error during file validation")
            return False

        logger.debug("File validation successful: %s", file_path)
        return True  # noqa: TRY300

    except OSError:
        logger.exception(
            "File validation failed - OS error accessing file %s",
            file_path,
        )
        logger.exception("This indicates a system-level issue preventing file access")
        return False
    except Exception:
        logger.exception(
            "File validation failed - unexpected error for file %s",
            file_path,
        )
        logger.exception("This indicates an internal error in the validation process")
        logger.exception("Please report this issue with the full error details")
        return False
