#!/usr/bin/env python3
"""
Script de visualisation de la base de données.
Affiche la structure et les relations des tables.
"""

import os
import sys
import psycopg2
from typing import List, Dict

# Configuration de la base de données
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'course_platform',
    'user': 'course_user',
    'password': 'course_password'
}

def connect_db():
    """Connexion à la base de données PostgreSQL."""
    try:
        return psycopg2.connect(**DATABASE_CONFIG)
    except psycopg2.Error as e:
        print(f"❌ Erreur de connexion: {e}")
        sys.exit(1)

def get_tables(conn) -> List[str]:
    """Récupère la liste des tables."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        return [row[0] for row in cur.fetchall()]

def get_table_structure(conn, table_name: str) -> List[Dict]:
    """Récupère la structure d'une table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = []
        for row in cur.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3],
                'max_length': row[4]
            })
        return columns

def get_foreign_keys(conn, table_name: str) -> List[Dict]:
    """Récupère les clés étrangères d'une table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = %s;
        """, (table_name,))
        
        return [
            {
                'column': row[0],
                'references_table': row[1],
                'references_column': row[2]
            }
            for row in cur.fetchall()
        ]

def count_records(conn, table_name: str) -> int:
    """Compte les enregistrements dans une table."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cur.fetchone()[0]

def display_database_overview(conn):
    """Affiche un aperçu complet de la base de données."""
    print("📊 APERÇU DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    tables = get_tables(conn)
    print(f"📋 {len(tables)} tables trouvées: {', '.join(tables)}")
    print()
    
    for table in tables:
        print(f"🗂️  TABLE: {table.upper()}")
        print("-" * 30)
        
        # Structure
        columns = get_table_structure(conn, table)
        print("📋 Colonnes:")
        for col in columns:
            type_info = col['type']
            if col['max_length']:
                type_info += f"({col['max_length']})"
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  • {col['name']}: {type_info} {nullable}")
        
        # Clés étrangères
        fks = get_foreign_keys(conn, table)
        if fks:
            print("🔗 Relations:")
            for fk in fks:
                print(f"  • {fk['column']} → {fk['references_table']}.{fk['references_column']}")
        
        # Nombre d'enregistrements
        count = count_records(conn, table)
        print(f"📊 Enregistrements: {count}")
        print()

def main():
    """Fonction principale."""
    print("🔍 VISUALISATEUR DE BASE DE DONNÉES")
    print("=" * 40)
    
    conn = connect_db()
    print("✅ Connexion établie")
    print()
    
    try:
        display_database_overview(conn)
    finally:
        conn.close()
        print("✅ Connexion fermée")

if __name__ == "__main__":
    main()