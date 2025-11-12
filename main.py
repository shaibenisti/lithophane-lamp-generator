#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lithophane Lamp Generator - Main Application Entry Point
Lithophane lamp creator with advanced image processing and 3D mesh generation.

This modular version provides:
- Intelligent image processing with face detection
- High-quality 3D cylinder generation
- Multilingual support (Hebrew/English)
- Comprehensive error handling and validation
- Configurable settings with YAML support
- Environment variable configuration
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Add src directory to Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Import application modules
try:
    from src.gui.language_manager import LanguageManager
    from src.core.settings import Settings, ConfigManager
    from src.gui.main_window import LampGeneratorApp
    from src.utils.validation import validate_processing_environment
except ImportError as e:
    print(f"Application module import error: {e}")
    print("Please ensure all source files are in the correct directories.")
    sys.exit(1)


def setup_logging(log_level: str = "INFO", log_to_file: bool = True, log_file: str = "lamp_generator.log") -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to file
        log_file: Log file name
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Get or create root logger
    root_logger = logging.getLogger()

    # Only configure if not already configured (avoid interfering with library logging)
    if not root_logger.handlers:
        # Setup handlers
        handlers = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)

        # File handler
        if log_to_file:
            try:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(numeric_level)
                file_handler.setFormatter(logging.Formatter(log_format))
                handlers.append(file_handler)
            except Exception as e:
                print(f"Warning: Could not create log file {log_file}: {e}")

        # Add handlers to root logger
        for handler in handlers:
            root_logger.addHandler(handler)

        root_logger.setLevel(numeric_level)
    else:
        # Logger already configured, just update level
        root_logger.setLevel(numeric_level)
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {'Yes' if log_to_file else 'No'}")


def load_environment_config() -> dict:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary with environment configuration
    """
    # Load .env file if it exists
    env_file = Path.cwd() / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment configuration from: {env_file}")
    
    # Get configuration with defaults
    config = {
        'opencv_threads': int(os.getenv('OPENCV_THREADS', '4')),
        'max_memory_gb': int(os.getenv('MAX_MEMORY_GB', '8')),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_to_file': os.getenv('LOG_TO_FILE', 'true').lower() == 'true',
        'log_file': os.getenv('LOG_FILE', 'lamp_generator.log'),
        'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
        'default_language': os.getenv('DEFAULT_LANGUAGE', 'he'),
        'auto_save_settings': os.getenv('AUTO_SAVE_SETTINGS', 'true').lower() == 'true',
    }
    
    return config


def validate_environment() -> bool:
    """
    Validate the processing environment and dependencies.
    
    Returns:
        True if environment is valid, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        validation_results = validate_processing_environment()
        
        # Check critical dependencies
        if not validation_results['opencv_available']:
            QMessageBox.critical(
                None, "Missing Dependencies", 
                "OpenCV is not available. Please install it with:\npip install opencv-python"
            )
            return False
        
        if not validation_results['numpy_available']:
            QMessageBox.critical(
                None, "Missing Dependencies", 
                "NumPy is not available. Please install it with:\npip install numpy"
            )
            return False
        
        if not validation_results['trimesh_available']:
            QMessageBox.critical(
                None, "Missing Dependencies", 
                "Trimesh is not available. Please install it with:\npip install trimesh"
            )
            return False
        
        # Log environment information
        logger.info(f"OpenCV version: {validation_results.get('opencv_version', 'Unknown')}")
        
        if validation_results['memory_available_gb'] > 0:
            logger.info(f"Available memory: {validation_results['memory_available_gb']:.1f} GB")
        
        # Show warnings if any
        for warning in validation_results['warnings']:
            logger.warning(f"Environment: {warning}")
        
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        QMessageBox.critical(
            None, "Environment Error", 
            f"Failed to validate processing environment:\n{e}"
        )
        return False


def load_application_settings(config_dir: Optional[Path] = None) -> Settings:
    """
    Load application settings from configuration files.
    
    Args:
        config_dir: Configuration directory (uses default if None)
        
    Returns:
        Loaded settings
    """
    logger = logging.getLogger(__name__)
    
    try:
        if config_dir is None:
            config_dir = Path.cwd() / 'config'
        
        config_manager = ConfigManager(config_dir)
        settings = config_manager.get_settings()
        
        logger.info(f"Settings loaded from: {config_manager.config_file}")
        return settings
        
    except Exception as e:
        logger.warning(f"Could not load settings file, using defaults: {e}")
        return Settings()


def create_application() -> QApplication:
    """
    Create and configure the Qt application.
    
    Returns:
        Configured QApplication instance
    """
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Lithophane Lamp Generator")
    app.setApplicationDisplayName("מחולל מנורות ליטופן")
    app.setOrganizationName("Professional 3D Solutions")
    app.setOrganizationDomain("lithophane-generator.local")
    app.setApplicationVersion("2.0.0")
    
    # High DPI support is enabled by default in PyQt6
    # AA_EnableHighDpiScaling is deprecated and not needed
    try:
        # Only set AA_UseHighDpiPixmaps if it exists (for compatibility)
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # Ignore if not available - high DPI support is automatic in PyQt6
        pass
    
    return app


def main() -> int:
    """
    Main application entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Load environment configuration
        env_config = load_environment_config()
        
        # Setup logging
        setup_logging(
            log_level=env_config['log_level'],
            log_to_file=env_config['log_to_file'],
            log_file=env_config['log_file']
        )
        
        logger = logging.getLogger(__name__)
        logger.info("=== Lithophane Lamp Generator Starting ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {Path.cwd()}")
        
        # Create Qt application
        app = create_application()
        
        # Validate processing environment
        if not validate_environment():
            logger.error("Environment validation failed")
            return 1
        
        # Load application settings
        settings = load_application_settings()
        
        # Apply environment overrides to settings
        if 'opencv_threads' in env_config:
            settings.opencv_threads = env_config['opencv_threads']
        
        logger.info("Application initialization completed successfully")
        
        # Create and show main window
        try:
            main_window = LampGeneratorApp(settings)
            
            # Set default language from environment
            if env_config['default_language'] in ['he', 'en']:
                main_window.language_manager.set_language(env_config['default_language'])
                main_window.update_ui_language()
                main_window.update_layout_direction()
            
            main_window.show()
            logger.info("Main window created and displayed")
            
        except Exception as e:
            logger.error(f"Failed to create main window: {e}", exc_info=True)
            QMessageBox.critical(
                None, "Application Error", 
                f"Failed to create main window:\n{e}\n\nPlease check the log file for details."
            )
            return 1
        
        # Run application event loop
        logger.info("Starting application event loop")
        exit_code = app.exec()
        
        logger.info(f"Application terminated with exit code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 130
        
    except Exception as e:
        # Handle any unexpected errors during startup
        try:
            logger = logging.getLogger(__name__)
            logger.critical(f"Fatal error during application startup: {e}", exc_info=True)
        except:
            # If logging fails, print to console
            print(f"Fatal error during application startup: {e}")
        
        try:
            QMessageBox.critical(
                None, "Fatal Error", 
                f"A fatal error occurred during application startup:\n{e}\n\n"
                "Please check the log file for details and contact support if the problem persists."
            )
        except:
            pass
        
        return 1


if __name__ == "__main__":
    # Set proper exit code handling
    exit_code = main()
    sys.exit(exit_code)