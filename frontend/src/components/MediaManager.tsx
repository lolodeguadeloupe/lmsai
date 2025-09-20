'use client';

import { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loading } from '@/components/ui/loading';
import { 
  CloudArrowUpIcon,
  PhotoIcon,
  FilmIcon,
  DocumentIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  FolderIcon,
  EyeIcon,
  TrashIcon,
  LinkIcon,
  ArrowDownTrayIcon,
  InformationCircleIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface MediaFile {
  id: string;
  name: string;
  type: 'image' | 'video' | 'document' | 'audio';
  url: string;
  size: number;
  uploadedAt: string;
  alt?: string;
  folder?: string;
}

interface MediaManagerProps {
  onSelect?: (file: MediaFile) => void;
  allowMultiple?: boolean;
  allowedTypes?: ('image' | 'video' | 'document' | 'audio')[];
  maxFileSize?: number; // in MB
  currentFolder?: string;
  showUpload?: boolean;
}

const MOCK_MEDIA: MediaFile[] = [
  {
    id: '1',
    name: 'course-banner.jpg',
    type: 'image',
    url: '/api/placeholder/800/400',
    size: 245760,
    uploadedAt: '2024-01-15T10:30:00Z',
    alt: 'Bannière de cours',
    folder: 'banners',
  },
  {
    id: '2',
    name: 'intro-video.mp4',
    type: 'video',
    url: '/api/placeholder/video/intro',
    size: 15728640,
    uploadedAt: '2024-01-14T14:20:00Z',
    folder: 'videos',
  },
  {
    id: '3',
    name: 'diagram.png',
    type: 'image',
    url: '/api/placeholder/600/400',
    size: 89600,
    uploadedAt: '2024-01-13T09:15:00Z',
    alt: 'Diagramme explicatif',
    folder: 'diagrams',
  },
  {
    id: '4',
    name: 'exercise.pdf',
    type: 'document',
    url: '/api/placeholder/document',
    size: 512000,
    uploadedAt: '2024-01-12T16:45:00Z',
    folder: 'documents',
  },
];

export default function MediaManager({
  onSelect,
  allowMultiple = false,
  allowedTypes = ['image', 'video', 'document', 'audio'],
  maxFileSize = 50,
  currentFolder = '',
  showUpload = true,
}: MediaManagerProps) {
  const [files, setFiles] = useState<MediaFile[]>(MOCK_MEDIA);
  const [selectedFiles, setSelectedFiles] = useState<MediaFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentFolderState, setCurrentFolderState] = useState(currentFolder);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = allowedTypes.includes(file.type);
    const matchesFolder = !currentFolderState || file.folder === currentFolderState;
    return matchesSearch && matchesType && matchesFolder;
  });

  const folders = Array.from(new Set(files.map(f => f.folder).filter(Boolean)));

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'image': return PhotoIcon;
      case 'video': return FilmIcon;
      case 'document': return DocumentIcon;
      default: return DocumentIcon;
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = async (fileList: File[]) => {
    const validFiles = fileList.filter(file => {
      const fileType = file.type.startsWith('image/') ? 'image' :
                      file.type.startsWith('video/') ? 'video' :
                      file.type.startsWith('audio/') ? 'audio' : 'document';
      
      if (!allowedTypes.includes(fileType as any)) {
        toast.error(`Type de fichier non autorisé: ${file.name}`);
        return false;
      }
      
      if (file.size > maxFileSize * 1024 * 1024) {
        toast.error(`Fichier trop volumineux: ${file.name} (max ${maxFileSize}MB)`);
        return false;
      }
      
      return true;
    });

    if (validFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];
        
        // Simuler l'upload
        for (let progress = 0; progress <= 100; progress += 10) {
          setUploadProgress(progress);
          await new Promise(resolve => setTimeout(resolve, 100));
        }

        const fileType = file.type.startsWith('image/') ? 'image' :
                        file.type.startsWith('video/') ? 'video' :
                        file.type.startsWith('audio/') ? 'audio' : 'document';

        const newFile: MediaFile = {
          id: `upload-${Date.now()}-${i}`,
          name: file.name,
          type: fileType as MediaFile['type'],
          url: URL.createObjectURL(file),
          size: file.size,
          uploadedAt: new Date().toISOString(),
          folder: currentFolderState || 'uploads',
        };

        setFiles(prev => [newFile, ...prev]);
      }

      toast.success(`${validFiles.length} fichier(s) uploadé(s) avec succès`);
    } catch (error) {
      toast.error('Erreur lors de l\'upload');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleSelect = (file: MediaFile) => {
    if (!allowMultiple) {
      setSelectedFiles([file]);
      onSelect?.(file);
    } else {
      setSelectedFiles(prev => {
        const isSelected = prev.find(f => f.id === file.id);
        if (isSelected) {
          return prev.filter(f => f.id !== file.id);
        } else {
          return [...prev, file];
        }
      });
    }
  };

  const handleDelete = (fileId: string) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce fichier ?')) {
      setFiles(prev => prev.filter(f => f.id !== fileId));
      setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
      toast.success('Fichier supprimé');
    }
  };

  const copyToClipboard = (url: string) => {
    navigator.clipboard.writeText(url);
    toast.success('URL copiée dans le presse-papiers');
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Gestionnaire de médias</h2>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            >
              {viewMode === 'grid' ? 'Liste' : 'Grille'}
            </Button>
            
            {showUpload && (
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                size="sm"
              >
                <CloudArrowUpIcon className="w-4 h-4 mr-2" />
                Upload
              </Button>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher des fichiers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <select
            value={currentFolderState}
            onChange={(e) => setCurrentFolderState(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Tous les dossiers</option>
            {folders.map(folder => (
              <option key={folder} value={folder}>{folder}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Upload Area */}
      {showUpload && (
        <div
          className={`m-4 p-8 border-2 border-dashed rounded-lg transition-colors ${
            dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={allowedTypes.map(type => {
              switch (type) {
                case 'image': return 'image/*';
                case 'video': return 'video/*';
                case 'audio': return 'audio/*';
                case 'document': return '.pdf,.doc,.docx,.txt';
                default: return '*/*';
              }
            }).join(',')}
            onChange={handleFileSelect}
            className="hidden"
          />
          
          <div className="text-center">
            <CloudArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">
              Glissez-déposez vos fichiers ici ou{' '}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                cliquez pour parcourir
              </button>
            </p>
            <p className="text-sm text-gray-500">
              Types autorisés: {allowedTypes.join(', ')} • Taille max: {maxFileSize}MB
            </p>
          </div>

          {isUploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Upload en cours...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Files Grid/List */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredFiles.length === 0 ? (
          <div className="text-center py-8">
            <PhotoIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun fichier</h3>
            <p className="text-gray-600">
              {searchQuery ? 'Aucun fichier ne correspond à votre recherche' : 'Aucun fichier dans ce dossier'}
            </p>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 
            'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4' : 
            'space-y-2'
          }>
            {filteredFiles.map(file => (
              <MediaFileCard
                key={file.id}
                file={file}
                isSelected={selectedFiles.some(f => f.id === file.id)}
                viewMode={viewMode}
                onSelect={() => handleSelect(file)}
                onDelete={() => handleDelete(file.id)}
                onCopyUrl={() => copyToClipboard(file.url)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {selectedFiles.length > 0 && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {selectedFiles.length} fichier(s) sélectionné(s)
            </span>
            
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedFiles([])}
              >
                Désélectionner
              </Button>
              
              {onSelect && !allowMultiple && selectedFiles.length === 1 && (
                <Button size="sm" onClick={() => onSelect(selectedFiles[0])}>
                  <CheckIcon className="w-4 h-4 mr-2" />
                  Utiliser ce fichier
                </Button>
              )}
              
              {onSelect && allowMultiple && (
                <Button size="sm" onClick={() => selectedFiles.forEach(onSelect)}>
                  <CheckIcon className="w-4 h-4 mr-2" />
                  Utiliser ces fichiers
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Media File Card Component
interface MediaFileCardProps {
  file: MediaFile;
  isSelected: boolean;
  viewMode: 'grid' | 'list';
  onSelect: () => void;
  onDelete: () => void;
  onCopyUrl: () => void;
}

function MediaFileCard({ file, isSelected, viewMode, onSelect, onDelete, onCopyUrl }: MediaFileCardProps) {
  const FileIcon = getFileIcon(file.type);
  
  if (viewMode === 'list') {
    return (
      <div className={`flex items-center p-3 border rounded-lg transition-colors cursor-pointer ${
        isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
      }`} onClick={onSelect}>
        <div className="flex-shrink-0 mr-3">
          {file.type === 'image' ? (
            <img src={file.url} alt={file.alt} className="w-10 h-10 object-cover rounded" />
          ) : (
            <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
              <FileIcon className="w-5 h-5 text-gray-600" />
            </div>
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-900 truncate">{file.name}</h3>
          <div className="flex items-center text-xs text-gray-500 space-x-4">
            <span>{formatFileSize(file.size)}</span>
            <span>{new Date(file.uploadedAt).toLocaleDateString('fr-FR')}</span>
            {file.folder && <span>{file.folder}</span>}
          </div>
        </div>
        
        <div className="flex items-center space-x-2 ml-4">
          <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); onCopyUrl(); }}>
            <LinkIcon className="w-3 h-3" />
          </Button>
          <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-red-600">
            <TrashIcon className="w-3 h-3" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <Card className={`overflow-hidden transition-all cursor-pointer ${
      isSelected ? 'ring-2 ring-blue-500' : 'hover:shadow-md'
    }`} onClick={onSelect}>
      <div className="aspect-square bg-gray-100 flex items-center justify-center">
        {file.type === 'image' ? (
          <img src={file.url} alt={file.alt} className="w-full h-full object-cover" />
        ) : (
          <FileIcon className="w-12 h-12 text-gray-400" />
        )}
      </div>
      
      <div className="p-3">
        <h3 className="text-sm font-medium text-gray-900 truncate mb-1">{file.name}</h3>
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{formatFileSize(file.size)}</span>
          <div className="flex space-x-1">
            <button onClick={(e) => { e.stopPropagation(); onCopyUrl(); }} className="hover:text-blue-600">
              <LinkIcon className="w-3 h-3" />
            </button>
            <button onClick={(e) => { e.stopPropagation(); onDelete(); }} className="hover:text-red-600">
              <TrashIcon className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}

function getFileIcon(type: string) {
  switch (type) {
    case 'image': return PhotoIcon;
    case 'video': return FilmIcon;
    case 'document': return DocumentIcon;
    default: return DocumentIcon;
  }
}