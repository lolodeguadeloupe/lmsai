# 🎨 Frontend - Plateforme de Création de Cours IA

Une interface moderne inspirée de Coursebox.ai pour la plateforme de génération de cours IA, construite avec Next.js, React et TailwindCSS.

## 🚀 Fonctionnalités Implémentées

### ✅ Pages Principales Complètes
- **Landing Page** (`/`) - Hero section moderne avec animations Framer Motion
- **Dashboard** (`/dashboard`) - Interface de gestion avec statistiques temps réel
- **Authentification** (`/auth/signin`, `/auth/signup`) - Système complet avec validation
- **Création de Cours** (`/courses/create`) - Wizard multi-étapes guidé par l'IA
- **Suivi de Génération** (`/courses/[id]/generation`) - Monitoring temps réel avec WebSocket
- **Visualisation de Cours** (`/courses/[id]`) - Interface complète avec onglets et exports

### 🎯 Composants UI Avancés
- **Design System** avec CVA (Class Variance Authority)
- **Composants Réutilisables** : Button, Card, Loading, etc.
- **CourseWizard** - Interface step-by-step pour création guidée
- **CoursePreview** - Prévisualisation temps réel pendant génération
- **ProgressTracker** - Suivi visuel des processus IA
- **QualityMetrics** - Affichage des scores pédagogiques

### 🔧 Architecture Technique
- **Next.js 14** avec App Router
- **TypeScript** pour la sécurité des types
- **TailwindCSS** + Headless UI pour le design
- **Zustand** pour la gestion d'état global
- **React Query** pour la gestion des données serveur
- **React Hook Form** + Zod pour la validation
- **Framer Motion** pour les animations
- **Axios** pour les appels API

### 🌟 Inspirations Design de Coursebox.ai
- **Palette de couleurs** : Gradients bleu/violet modernes
- **Typographie** : Inter pour une lisibilité optimale
- **Layout responsive** : Mobile-first avec grilles flexibles
- **Animations fluides** : Transitions et micro-interactions
- **CTA prominents** : Boutons d'action bien visibles

## 🔗 Intégration Backend API

### Endpoints Intégrés
```typescript
// Cours
GET    /api/v1/courses          // Liste des cours
POST   /api/v1/courses          // Création de cours
GET    /api/v1/courses/:id      // Détails d'un cours
PUT    /api/v1/courses/:id      // Modification
DELETE /api/v1/courses/:id      // Suppression

// Génération
GET    /api/v1/courses/:id/generation-status  // Statut de génération
GET    /api/v1/courses/:id/quality-metrics    // Métriques de qualité
POST   /api/v1/courses/:id/export            // Export (SCORM, xAPI, PDF)

// Catégories
GET    /api/v1/categories       // Liste des catégories

// Chapitres
GET    /api/v1/chapters/:id     // Détails d'un chapitre
PUT    /api/v1/chapters/:id     // Modification
```

### Types TypeScript Complets
```typescript
interface Course {
  id: string;
  title: string;
  description: string;
  status: 'draft' | 'generating' | 'published' | 'archived';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  // ... autres propriétés
}

interface GenerationStatus {
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress_percentage: number;
  current_phase: string;
  estimated_time_remaining: string;
}
```

## 🎭 Expérience Utilisateur

### Flux de Création de Cours
1. **Landing Page** → Découverte et inscription
2. **Dashboard** → Vue d'ensemble des cours existants
3. **Course Wizard** → Création guidée en 3 étapes :
   - Informations de base (titre, description, niveau)
   - Catégorie et mots-clés
   - Configuration IA (prompt détaillé)
4. **Page de Génération** → Suivi temps réel avec :
   - Barre de progression animée
   - Étapes de génération visualisées
   - Prévisualisation du contenu généré
5. **Course Viewer** → Visualisation complète avec :
   - Onglets (Vue d'ensemble, Chapitres, Analytics)
   - Métriques de qualité
   - Options d'export multiples

### Features UX Avancées
- **Validation temps réel** avec messages d'erreur clairs
- **Feedback visuel** pour toutes les actions utilisateur
- **États de chargement** avec spinners et squelettes
- **Toasts notifications** pour les succès/erreurs
- **Shortcuts clavier** dans les formulaires
- **Accessibilité** avec ARIA labels et navigation clavier

## 🏗️ Structure du Projet

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx           # Landing page
│   │   ├── dashboard/         # Dashboard principal
│   │   ├── auth/             # Pages d'authentification
│   │   └── courses/          # Gestion des cours
│   ├── components/           # Composants réutilisables
│   │   ├── ui/              # Design system de base
│   │   ├── CoursePreview.tsx # Prévisualisation temps réel
│   │   └── Navigation.tsx    # Navigation principale
│   ├── lib/                  # Utilitaires et configuration
│   │   ├── api.ts           # Client API avec Axios
│   │   ├── hooks/           # React hooks personnalisés
│   │   └── utils.ts         # Fonctions utilitaires
│   ├── store/               # Gestion d'état Zustand
│   ├── styles/              # Styles globaux
│   └── types/               # Types TypeScript
├── public/                   # Assets statiques
└── package.json             # Dépendances
```

## 🎨 Design System

### Couleurs Principales
```css
:root {
  --primary-50: #eff6ff;
  --primary-600: #2563eb;
  --primary-700: #1d4ed8;
  --secondary-600: #7c3aed;
  --success-600: #059669;
  --error-600: #dc2626;
}
```

### Composants Button avec Variants
```typescript
// Exemple d'utilisation
<Button variant="default" size="lg">Créer un cours</Button>
<Button variant="outline" size="sm">Voir détails</Button>
<Button variant="ghost">Action secondaire</Button>
```

## 🚀 Démarrage Rapide

```bash
# Installation des dépendances
npm install

# Développement
npm run dev

# Build production
npm run build
npm start

# Tests
npm run test

# Linting
npm run lint
```

## 🔧 Configuration

### Variables d'Environnement
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
NEXT_PUBLIC_API_KEY=test-api-key
```

### Points de Configuration
- **API Client** : `src/lib/api.ts`
- **Styles globaux** : `src/styles/globals.css`
- **Configuration Tailwind** : `tailwind.config.js`
- **Configuration TypeScript** : `tsconfig.json`

## 📱 Responsive Design

- **Mobile First** : Design optimisé pour mobile d'abord
- **Breakpoints** : sm (640px), md (768px), lg (1024px), xl (1280px)
- **Grilles flexibles** : CSS Grid + Flexbox pour tous les layouts
- **Touch friendly** : Boutons et zones tactiles optimisées

## 🎯 Optimisations

### Performance
- **Code splitting** automatique avec Next.js
- **Lazy loading** des images et composants
- **React Query** avec cache intelligent
- **Bundle optimization** avec analyse automatique

### SEO
- **Métadonnées** dynamiques par page
- **Structure sémantique** HTML5
- **Open Graph** tags pour réseaux sociaux
- **Schema.org** markup pour les cours

## 🔮 Améliorations Futures

### Fonctionnalités Prévues
- [ ] Mode sombre / clair
- [ ] Notifications push en temps réel
- [ ] Collaboration multi-utilisateurs
- [ ] Système de commentaires
- [ ] Intégration vidéo/audio
- [ ] Mode hors-ligne avec PWA
- [ ] Tests A/B intégrés
- [ ] Analytics utilisateur avancées

### Optimisations Techniques
- [ ] Micro-frontends pour la scalabilité
- [ ] WebAssembly pour l'IA côté client
- [ ] Service Worker pour la performance
- [ ] GraphQL pour l'optimisation des requêtes

## 🤝 Contribution

Le frontend est conçu pour être facilement extensible :

1. **Composants modulaires** : Chaque composant est autonome
2. **Types stricts** : TypeScript pour éviter les erreurs
3. **Tests unitaires** : Jest + Testing Library
4. **Documentation** : Storybook pour les composants UI

---

🎉 **Frontend complet et prêt pour la production !**

Interface moderne inspirée de Coursebox.ai avec toutes les fonctionnalités nécessaires pour créer et gérer des cours avec l'IA.