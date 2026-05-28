# engine/parser_manager.py
"""
Parser Manager - Manages bank parsers, including user-created ones.

Features:
- Load built-in parsers
- Load user-created parsers from user_parsers directory
- Add new parsers dynamically
- Test parsers against sample data
"""

import importlib
import json
import os
import sys
import inspect
from typing import Dict, List, Optional, Callable


class ParserManager:
    """Manages bank parsers - loading, registration, and user customization."""
    
    CONFIG_FILE = "parsers_config.json"
    USER_PARSERS_DIR = "user_parsers"
    
    def __init__(self):
        self.parsers: Dict[str, Dict] = {}
        self._extract_functions: Dict[str, Callable] = {}
        self._load_config()
        self._load_builtin_parsers()
        self._load_user_parsers()
    
    def _get_config_path(self):
        """Get path to configuration file"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), self.CONFIG_FILE)
    
    def _get_user_parsers_dir(self):
        """Get path to user parsers directory"""
        return os.path.join(os.path.dirname(__file__), self.USER_PARSERS_DIR)
    
    def _load_config(self):
        """Load parser configuration from JSON"""
        config_path = self._get_config_path()
        
        if not os.path.exists(config_path):
            self._create_default_config(config_path)
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for bank in config.get('banks', []):
                if bank.get('enabled', True):
                    self.parsers[bank['id']] = bank
                    
        except Exception as e:
            print(f"Error loading parser config: {e}")
    
    def _create_default_config(self, path):
        """Create default configuration file"""
        default_config = {
            "version": "1.0",
            "banks": [
                {
                    "id": "sbi_current",
                    "name": "State Bank of India (SBI)",
                    "module_path": "engine.banks.sbi_current",
                    "extract_function": "extract",
                    "built_in": True,
                    "enabled": True
                }
            ]
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(default_config, f, indent=4)
    
    def _load_builtin_parsers(self):
        """Load built-in parsers"""
        builtin_parsers = [
            ('sbi_current', 'engine.banks.sbi_current', 'State Bank of India (SBI)'),
            # Add more built-in parsers here as they are created:
            # ('city_union', 'engine.banks.city_union', 'City Union Bank'),
            # ('hdfc', 'engine.banks.hdfc', 'HDFC Bank'),
        ]
        
        for parser_id, module_path, name in builtin_parsers:
            if parser_id not in self.parsers:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, 'extract'):
                        self._extract_functions[parser_id] = module.extract
                        
                        # Get bank name from module if available
                        bank_name = getattr(module, 'BANK_NAME', name)
                        
                        self.parsers[parser_id] = {
                            'id': parser_id,
                            'name': bank_name,
                            'module_path': module_path,
                            'built_in': True,
                            'enabled': True
                        }
                        print(f"Loaded built-in parser: {bank_name}")
                except ImportError as e:
                    print(f"Could not load built-in parser {parser_id}: {e}")
    
    def _load_user_parsers(self):
        """Load user-created parsers from user_parsers directory"""
        user_parsers_path = self._get_user_parsers_dir()
        
        if not os.path.exists(user_parsers_path):
            os.makedirs(user_parsers_path, exist_ok=True)
            # Create __init__.py
            init_file = os.path.join(user_parsers_path, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# User-created bank parsers\n')
            return
        
        # Import all .py files in user_parsers directory
        for filename in os.listdir(user_parsers_path):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                try:
                    module_path = f"engine.banks.user_parsers.{module_name}"
                    
                    # Reload if already imported
                    if module_path in sys.modules:
                        module = importlib.reload(sys.modules[module_path])
                    else:
                        module = importlib.import_module(module_path)
                    
                    if hasattr(module, 'extract'):
                        parser_id = module_name
                        self._extract_functions[parser_id] = module.extract
                        
                        # Get bank name from module if available
                        bank_name = getattr(module, 'BANK_NAME', module_name.replace('_', ' ').title())
                        
                        self.parsers[parser_id] = {
                            'id': parser_id,
                            'name': bank_name,
                            'module_path': module_path,
                            'built_in': False,
                            'enabled': True
                        }
                        
                        print(f"Loaded user parser: {bank_name}")
                        
                except Exception as e:
                    print(f"Error loading user parser {filename}: {e}")
    
    def get_extract_function(self, bank_id: str) -> Optional[Callable]:
        """
        Get extraction function for a bank.
        
        Args:
            bank_id: Bank identifier
            
        Returns:
            Callable extract function or None
        """
        # Check cache first
        if bank_id in self._extract_functions:
            return self._extract_functions[bank_id]
        
        # Try to load from config
        parser_config = self.parsers.get(bank_id)
        if not parser_config:
            return None
        
        try:
            module = importlib.import_module(parser_config['module_path'])
            func_name = parser_config.get('extract_function', 'extract')
            func = getattr(module, func_name)
            self._extract_functions[bank_id] = func
            return func
        except Exception as e:
            print(f"Error loading parser {bank_id}: {e}")
            return None
    
    def get_bank_name(self, bank_id: str) -> str:
        """
        Get display name for a bank.
        
        Args:
            bank_id: Bank identifier
            
        Returns:
            Display name string
        """
        parser = self.parsers.get(bank_id, {})
        return parser.get('name', bank_id)
    
    def get_all_banks(self) -> List[Dict]:
        """
        Get list of all available banks.
        
        Returns:
            List of dicts with 'id', 'name', 'built_in' keys
        """
        return [
            {
                'id': p['id'],
                'name': p.get('name', p['id']),
                'built_in': p.get('built_in', False)
            }
            for p in self.parsers.values()
            if p.get('enabled', True)
        ]
    
    def add_user_parser(self, parser_id: str, bank_name: str, file_content: str) -> Dict:
        """
        Add a new user parser from file content.
        
        Args:
            parser_id: Unique identifier for the parser
            bank_name: Display name for the bank
            file_content: Python code for the parser
            
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'error': str (if failed),
                'test_results': dict (if test_parser exists)
            }
        """
        try:
            # Validate the content has required function
            if 'def extract(' not in file_content:
                return {
                    'success': False,
                    'error': 'Parser must contain a function: def extract(narration)'
                }
            
            # Save to user_parsers directory
            user_parsers_path = self._get_user_parsers_dir()
            os.makedirs(user_parsers_path, exist_ok=True)
            
            file_path = os.path.join(user_parsers_path, f"{parser_id}.py")
            
            with open(file_path, 'w') as f:
                f.write(file_content)
            
            # Try to load and test it
            module_path = f"engine.banks.user_parsers.{parser_id}"
            
            # Reload if already imported
            if module_path in sys.modules:
                importlib.reload(sys.modules[module_path])
            
            module = importlib.import_module(module_path)
            
            if not hasattr(module, 'extract'):
                return {
                    'success': False,
                    'error': 'Parser loaded but extract function not found'
                }
            
            # Run tests if test_parser function exists
            test_results = None
            if hasattr(module, 'test_parser'):
                try:
                    test_results = module.test_parser()
                except Exception as e:
                    test_results = {'error': str(e)}
            
            # Add to loaded parsers
            self._extract_functions[parser_id] = module.extract
            self.parsers[parser_id] = {
                'id': parser_id,
                'name': bank_name,
                'module_path': module_path,
                'built_in': False,
                'enabled': True
            }
            
            # Update config
            self._update_config(parser_id, bank_name, module_path)
            
            return {
                'success': True,
                'message': f'Parser for {bank_name} added successfully',
                'test_results': test_results
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_parser(self, parser_id: str) -> Dict:
        """
        Test a parser against its test cases.
        
        Args:
            parser_id: Parser identifier
            
        Returns:
            dict: {
                'success': bool,
                'results': dict (if successful),
                'error': str (if failed)
            }
        """
        try:
            parser_config = self.parsers.get(parser_id)
            if not parser_config:
                return {'success': False, 'error': 'Parser not found'}
            
            module = importlib.import_module(parser_config['module_path'])
            
            if hasattr(module, 'test_parser'):
                return {
                    'success': True,
                    'results': module.test_parser()
                }
            else:
                return {
                    'success': False,
                    'error': 'Parser does not have test_parser function'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_parser_source(self, parser_id: str) -> Optional[str]:
        """
        Get source code of a parser.
        
        Args:
            parser_id: Parser identifier
            
        Returns:
            Source code string or None
        """
        try:
            parser_config = self.parsers.get(parser_id)
            if not parser_config:
                return None
            
            module = importlib.import_module(parser_config['module_path'])
            return inspect.getsource(module)
            
        except Exception as e:
            print(f"Error getting parser source: {e}")
            return None
    
    def export_parser(self, parser_id: str, filepath: str) -> Dict:
        """
        Export parser to a file.
        
        Args:
            parser_id: Parser identifier
            filepath: Output file path
            
        Returns:
            dict: {'success': bool, 'error': str (if failed)}
        """
        try:
            source = self.get_parser_source(parser_id)
            if source is None:
                return {'success': False, 'error': 'Could not get parser source'}
            
            with open(filepath, 'w') as f:
                f.write(source)
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _update_config(self, parser_id: str, bank_name: str, module_path: str):
        """
        Update configuration file with new parser.
        
        Args:
            parser_id: Parser identifier
            bank_name: Display name
            module_path: Python module path
        """
        config_path = self._get_config_path()
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {'version': '1.0', 'banks': []}
            
            # Check if already exists
            existing = [b for b in config['banks'] if b['id'] == parser_id]
            if existing:
                # Update existing
                for b in config['banks']:
                    if b['id'] == parser_id:
                        b['name'] = bank_name
                        b['module_path'] = module_path
                        break
            else:
                config['banks'].append({
                    'id': parser_id,
                    'name': bank_name,
                    'module_path': module_path,
                    'extract_function': 'extract',
                    'built_in': False,
                    'enabled': True
                })
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            print(f"Error updating config: {e}")
    
    def reload_parsers(self):
        """Reload all parsers"""
        self._extract_functions.clear()
        self.parsers.clear()
        self._load_config()
        self._load_builtin_parsers()
        self._load_user_parsers()
    
    def remove_user_parser(self, parser_id: str) -> Dict:
        """
        Remove a user parser.
        
        Args:
            parser_id: Parser identifier
            
        Returns:
            dict: {'success': bool, 'error': str (if failed)}
        """
        try:
            parser = self.parsers.get(parser_id)
            if not parser:
                return {'success': False, 'error': 'Parser not found'}
            
            if parser.get('built_in'):
                return {'success': False, 'error': 'Cannot remove built-in parser'}
            
            # Remove file
            user_parsers_path = self._get_user_parsers_dir()
            file_path = os.path.join(user_parsers_path, f"{parser_id}.py")
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove from loaded parsers
            del self.parsers[parser_id]
            if parser_id in self._extract_functions:
                del self._extract_functions[parser_id]
            
            # Remove from sys.modules
            module_path = parser.get('module_path')
            if module_path and module_path in sys.modules:
                del sys.modules[module_path]
            
            # Update config
            config_path = self._get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                config['banks'] = [b for b in config['banks'] if b['id'] != parser_id]
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Singleton instance
_parser_manager = None


def get_parser_manager() -> ParserManager:
    """
    Get singleton parser manager instance.
    
    Returns:
        ParserManager instance
    """
    global _parser_manager
    if _parser_manager is None:
        _parser_manager = ParserManager()
    return _parser_manager