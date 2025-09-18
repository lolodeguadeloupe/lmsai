# PreToolUse Hook - Protection contre les actions dangereuses

## Vue d'ensemble

Ce hook de sécurité analyse les appels d'outils avant leur exécution pour détecter et bloquer les actions potentiellement dangereuses ou destructrices.

## Fichiers

- `pre-tool-use-hook.py` - Le hook principal
- `test-hook.py` - Script de tests automatisés
- `README-hook.md` - Cette documentation

## Installation et configuration

### 1. Rendre le hook exécutable
```bash
chmod +x scripts/pre-tool-use-hook.py
```

### 2. Configuration dans Claude Code
Ajoutez cette configuration dans votre fichier de paramètres Claude Code (`.claude/settings.local.json`) :

```json
{
  "permissions": {
    "allow": ["Bash(python3:*)"],
    "deny": [],
    "ask": []
  },
  "hooks": {
    "pre-tool-use": {
      "command": ["python3", "scripts/pre-tool-use-hook.py"],
      "enabled": true
    }
  }
}
```

## Protections implémentées

### 🚨 Commandes système dangereuses
- **Suppression destructrice** : `rm -rf /`, `rm /*`
- **Modifications de permissions** : `chmod 777`, `chown root`
- **Formatage de disques** : `mkfs`, `fdisk`, `dd`
- **Contrôle des services** : `systemctl stop/disable`, `service stop`
- **Arrêt système** : `shutdown`, `reboot`, `halt`
- **Montage/démontage** : `mount`, `umount`
- **Exécution de scripts distants** : `curl ... | bash`, `wget ... | sh`

### 🔒 Fichiers sensibles protégés
- **Fichiers système** : `/etc/passwd`, `/etc/shadow`, `/etc/hosts`
- **Clés SSH** : `~/.ssh/id_rsa`, `~/.ssh/id_ed25519`
- **Configuration** : `.env`, `config.json`, `settings.py`
- **Répertoires système** : `/var/log/`, `/tmp/`, `/dev/`

### 💾 Patterns SQL dangereux
- **Suppression** : `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- **Suppression massive** : `DELETE FROM ... WHERE 1=1`
- **Modification massive** : `UPDATE ... SET ... WHERE 1=1`
- **Exécution dynamique** : `EXEC()`, `EXECUTE()`

### 🌐 URLs potentiellement dangereuses
- **Accès fichiers locaux** : `file://`
- **Ports sensibles** : `localhost:22` (SSH), `localhost:3389` (RDP)
- **Protocoles risqués** : `ftp://`

## Utilisation

### Exécution manuelle pour test
```bash
# Test d'une commande dangereuse
echo '{"tool_name": "Bash", "parameters": {"command": "rm -rf /"}}' | python3 scripts/pre-tool-use-hook.py

# Réponse attendue : action "block" avec message d'alerte
```

### Tests automatisés
```bash
# Lancer tous les tests
python3 scripts/test-hook.py

# Les tests couvrent 16 scénarios différents
```

## Réponses du hook

### Action autorisée
```json
{
  "action": "allow"
}
```

### Action bloquée
```json
{
  "action": "block",
  "message": "🚨 Action dangereuse bloquée: [détails]\n\nPour continuer, vérifiez que cette action est intentionnelle et sûre."
}
```

### Erreur
```json
{
  "action": "block",
  "message": "Erreur dans le hook de sécurité: [détails]"
}
```

## Personnalisation

### Ajouter de nouvelles protections

1. **Commandes dangereuses** - Modifier `dangerous_commands` dans `DangerousActionDetector`
2. **Fichiers sensibles** - Ajouter des patterns dans `sensitive_files`
3. **Extensions critiques** - Compléter `critical_extensions`
4. **Patterns SQL** - Étendre `dangerous_sql_patterns`

### Exemple d'ajout
```python
# Ajouter une nouvelle commande dangereuse
self.dangerous_commands['newcmd'] = ['dangerous_arg1', 'dangerous_arg2']

# Ajouter un pattern de fichier sensible
self.sensitive_files.append(r'\.secret$')
```

## Limitations

1. **Analyse statique** - Ne détecte que les patterns connus
2. **Faux positifs** - Peut bloquer des actions légitimes similaires
3. **Contournement** - Scripts complexes peuvent échapper à la détection
4. **Performance** - Ajoute une latence à chaque appel d'outil

## Maintenance

- **Tests réguliers** : Exécuter `test-hook.py` après modifications
- **Mise à jour** : Ajouter de nouveaux patterns selon les besoins
- **Monitoring** : Surveiller les logs pour identifier les faux positifs

## Sécurité

Ce hook offre une protection de base mais ne remplace pas :
- Les bonnes pratiques de sécurité
- La vigilance lors de l'exécution de commandes
- Les sauvegardes régulières
- Les tests en environnement isolé