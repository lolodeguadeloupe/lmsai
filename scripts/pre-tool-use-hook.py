#!/usr/bin/env python3
"""
PreToolUse Hook for Claude Code - Protection contre les actions dangereuses

Ce hook vérifie les commandes et paramètres avant exécution pour prévenir
les actions potentiellement dangereuses ou destructrices.
"""

import sys
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class DangerousActionDetector:
    """Détecteur d'actions potentiellement dangereuses"""
    
    def __init__(self):
        # Commandes système dangereuses
        self.dangerous_commands = {
            'rm': ['/', '/home', '/usr', '/var', '/etc', '/boot', '/sys', '/proc'],
            'chmod': ['777', '+x /'],
            'chown': ['root', 'www-data'],
            'dd': ['if=/dev/zero', 'of=/dev/'],
            'mkfs': [],
            'fdisk': [],
            'parted': [],
            'systemctl': ['stop', 'disable'],
            'service': ['stop'],
            'kill': ['-9'],
            'killall': [],
            'shutdown': [],
            'reboot': [],
            'halt': [],
            'poweroff': [],
            'mount': [],
            'umount': [],
            'crontab': ['-r'],
            'sudo': ['rm', 'chmod 777', 'chown'],
            'curl': ['| bash', '| sh'],
            'wget': ['| bash', '| sh'],
            'apt': ['remove', 'purge'],
            'npm': ['uninstall -g'],
            'pip': ['uninstall'],
            'docker': ['system prune', 'container rm', 'image rm'],
            'git': ['reset --hard', 'clean -fd'],
        }
        
        # Patterns de fichiers sensibles
        self.sensitive_files = [
            r'/etc/passwd', r'/etc/shadow', r'/etc/hosts',
            r'/home/[^/]+/\.ssh/', r'\.ssh/id_rsa', r'\.ssh/id_ed25519',
            r'\.env', r'\.config', r'config\.json', r'settings\.py',
            r'package\.json', r'requirements\.txt', r'Dockerfile',
            r'/var/log/', r'/tmp/', r'/dev/',
        ]
        
        # Extensions de fichiers critiques
        self.critical_extensions = [
            '.sh', '.bash', '.zsh', '.fish',
            '.ps1', '.bat', '.cmd',
            '.py', '.js', '.ts',
            '.sql', '.db', '.sqlite',
        ]
        
        # Patterns SQL dangereux
        self.dangerous_sql_patterns = [
            r'DROP\s+TABLE', r'DROP\s+DATABASE', r'TRUNCATE',
            r'DELETE\s+FROM.*WHERE\s+1=1', r'DELETE\s+FROM\s+[^W].*[^W]$',
            r'UPDATE.*SET.*WHERE\s+1=1', r'ALTER\s+TABLE.*DROP',
            r'EXEC\s*\(', r'EXECUTE\s*\(',
        ]

    def check_bash_command(self, command: str) -> Optional[str]:
        """Vérifie si une commande bash est dangereuse"""
        command_lower = command.lower().strip()
        
        # Vérifier les commandes dangereuses
        for cmd, dangerous_args in self.dangerous_commands.items():
            if command_lower.startswith(f"{cmd} ") or command_lower == cmd:
                if not dangerous_args:
                    return f"Commande potentiellement dangereuse détectée: {cmd}"
                
                for arg in dangerous_args:
                    if arg in command_lower:
                        return f"Commande dangereuse détectée: {cmd} avec argument '{arg}'"
        
        # Vérifier spécifiquement les commandes sudo
        if command_lower.startswith('sudo '):
            sudo_cmd = command_lower[5:].strip()  # Enlever "sudo "
            # Récursion pour vérifier la commande après sudo
            sudo_check = self.check_bash_command(sudo_cmd)
            if sudo_check:
                return f"Commande sudo dangereuse: {sudo_check}"
        
        # Vérifier les redirections dangereuses
        if re.search(r'>\s*/dev/', command_lower):
            return "Redirection vers /dev/ détectée - potentiellement dangereuse"
        
        # Vérifier les pipes vers des interpréteurs
        if re.search(r'\|\s*(bash|sh|python|node)', command_lower):
            return "Pipe vers un interpréteur détecté - potentiellement dangereux"
        
        # Vérifier les wildcards dangereux
        if re.search(r'rm.*\*.*/', command_lower):
            return "Suppression récursive avec wildcard détectée"
        
        return None

    def check_file_operations(self, tool_name: str, params: Dict[str, Any]) -> Optional[str]:
        """Vérifie les opérations sur fichiers"""
        if tool_name in ['Write', 'Edit', 'MultiEdit']:
            file_path = params.get('file_path', '')
            
            # Vérifier les fichiers système sensibles
            for pattern in self.sensitive_files:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return f"Modification de fichier sensible détectée: {file_path}"
            
            # Vérifier les extensions critiques en dehors du projet
            if not file_path.startswith('/home/laurent/mesprojets/'):
                for ext in self.critical_extensions:
                    if file_path.endswith(ext):
                        return f"Modification de fichier critique hors projet: {file_path}"
        
        # Vérifier le contenu pour les scripts
        if tool_name in ['Write', 'Edit'] and 'content' in params:
            content = params['content']
            
            # Vérifier les patterns SQL dangereux
            for pattern in self.dangerous_sql_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return f"Pattern SQL dangereux détecté: {pattern}"
            
            # Vérifier les commandes système dans le contenu
            bash_check = self.check_bash_command(content)
            if bash_check:
                return f"Contenu dangereux dans le fichier: {bash_check}"
        
        return None

    def check_network_operations(self, tool_name: str, params: Dict[str, Any]) -> Optional[str]:
        """Vérifie les opérations réseau"""
        if tool_name == 'WebFetch':
            url = params.get('url', '')
            
            # URLs potentiellement dangereuses
            dangerous_domains = [
                'localhost:22', 'localhost:3389', 
                '127.0.0.1:22', '127.0.0.1:3389',
                'file://', 'ftp://'
            ]
            
            for domain in dangerous_domains:
                if domain in url.lower():
                    return f"URL potentiellement dangereuse: {url}"
        
        return None

    def analyze_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Optional[str]:
        """Analyse un appel d'outil pour détecter les dangers"""
        
        # Vérifier les commandes bash
        if tool_name == 'Bash':
            command = params.get('command', '')
            return self.check_bash_command(command)
        
        # Vérifier les opérations sur fichiers
        file_check = self.check_file_operations(tool_name, params)
        if file_check:
            return file_check
        
        # Vérifier les opérations réseau
        network_check = self.check_network_operations(tool_name, params)
        if network_check:
            return network_check
        
        return None

def main():
    """Point d'entrée principal du hook"""
    try:
        # Lire les données du hook depuis stdin
        hook_data = json.loads(sys.stdin.read())
        
        tool_name = hook_data.get('tool_name', '')
        parameters = hook_data.get('parameters', {})
        
        # Initialiser le détecteur
        detector = DangerousActionDetector()
        
        # Analyser l'appel d'outil
        warning = detector.analyze_tool_call(tool_name, parameters)
        
        if warning:
            # Action dangereuse détectée
            response = {
                "action": "block",
                "message": f"🚨 Action dangereuse bloquée: {warning}\n\nPour continuer, vérifiez que cette action est intentionnelle et sûre."
            }
        else:
            # Action considérée comme sûre
            response = {
                "action": "allow"
            }
        
        # Retourner la réponse
        print(json.dumps(response))
        return 0
        
    except json.JSONDecodeError:
        # Erreur de décodage JSON
        response = {
            "action": "block",
            "message": "Erreur: Impossible de décoder les données du hook"
        }
        print(json.dumps(response))
        return 1
        
    except Exception as e:
        # Erreur inattendue
        response = {
            "action": "block", 
            "message": f"Erreur dans le hook de sécurité: {str(e)}"
        }
        print(json.dumps(response))
        return 1

if __name__ == "__main__":
    sys.exit(main())