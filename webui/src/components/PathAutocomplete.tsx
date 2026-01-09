/**
 * PathAutocomplete Component
 *
 * Provides inline file path autocomplete for the chat input.
 * Triggers when user types @ followed by a path prefix.
 * Supports Tab/Enter to select, Escape to dismiss, arrow keys to navigate.
 */

import { useState, useEffect, useCallback, useRef, forwardRef, useImperativeHandle } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Folder, File, FileText, FileCode, FileImage, X } from 'lucide-react';
import { createAbortableFetch, isAbortError } from '../utils/fetchWithAbort';

interface PathSuggestion {
  path: string;
  name: string;
  is_dir: boolean;
}

interface AutocompleteResponse {
  suggestions: PathSuggestion[];
  error?: string;
}

interface PathAutocompleteProps {
  /** The input value to monitor for @ triggers */
  inputValue: string;
  /** Callback when a path is selected */
  onSelect: (fullPath: string, suffix?: ':w') => void;
  /** Callback when input should be updated */
  onInputChange: (newValue: string) => void;
  /** Whether the autocomplete is enabled */
  enabled?: boolean;
  /** Base path for resolving relative paths */
  basePath?: string;
}

export interface PathAutocompleteHandle {
  /** Handle keyboard events from parent input */
  handleKeyDown: (e: React.KeyboardEvent) => boolean;
  /** Check if autocomplete is currently showing */
  isShowing: () => boolean;
}

// File icon based on extension
function getFileIcon(name: string, isDir: boolean) {
  if (isDir) return Folder;

  const ext = name.split('.').pop()?.toLowerCase() || '';
  const codeExts = ['js', 'jsx', 'ts', 'tsx', 'py', 'rs', 'go', 'java', 'cpp', 'c', 'h', 'rb', 'php'];
  const imageExts = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'];
  const docExts = ['md', 'txt', 'rst', 'doc', 'docx', 'pdf'];

  if (codeExts.includes(ext)) return FileCode;
  if (imageExts.includes(ext)) return FileImage;
  if (docExts.includes(ext)) return FileText;
  return File;
}

export const PathAutocomplete = forwardRef<PathAutocompleteHandle, PathAutocompleteProps>(
  function PathAutocomplete(
    { inputValue, onSelect, onInputChange, enabled = true, basePath },
    ref
  ) {
    const [suggestions, setSuggestions] = useState<PathSuggestion[]>([]);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [isVisible, setIsVisible] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [atPosition, setAtPosition] = useState<number | null>(null);
    const [showWriteSuffix, setShowWriteSuffix] = useState(false);

    const abortRef = useRef<(() => void) | null>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Find the @ trigger and extract the path prefix
    const findAtTrigger = useCallback((value: string): { position: number; prefix: string } | null => {
      // Find the last unescaped @ character
      for (let i = value.length - 1; i >= 0; i--) {
        if (value[i] === '@') {
          // Check if escaped
          if (i > 0 && value[i - 1] === '\\') continue;

          // Extract prefix after @
          const prefix = value.substring(i + 1);

          // Don't trigger if there's a space before more content (completed path)
          if (prefix.includes(' ') && !prefix.endsWith(' ')) {
            // Check if this looks like a complete path reference
            const spaceIdx = prefix.indexOf(' ');
            const beforeSpace = prefix.substring(0, spaceIdx);
            if (beforeSpace.includes('/') || beforeSpace.startsWith('~')) {
              return null; // Already completed
            }
          }

          // Don't trigger if already has :w suffix
          if (prefix.endsWith(':w')) return null;

          return { position: i, prefix: prefix.trim() };
        }
      }
      return null;
    }, []);

    // Fetch suggestions from API
    const fetchSuggestions = useCallback(async (prefix: string) => {
      // Cancel previous request
      if (abortRef.current) {
        abortRef.current();
      }

      // If no prefix or doesn't start with path indicators, default to home directory
      if (!prefix || (!prefix.startsWith('/') && !prefix.startsWith('~') && !prefix.startsWith('.'))) {
        prefix = '~/';
      }

      setIsLoading(true);

      const params = new URLSearchParams({ prefix });
      if (basePath) {
        params.append('base_path', basePath);
      }

      const { promise, abort } = createAbortableFetch<AutocompleteResponse>(
        `/api/path/autocomplete?${params.toString()}`,
        { timeout: 5000 }
      );

      abortRef.current = abort;

      try {
        const data = await promise;
        if (data.suggestions) {
          setSuggestions(data.suggestions);
          setSelectedIndex(0);
          setIsVisible(data.suggestions.length > 0);
        }
      } catch (err) {
        if (!isAbortError(err)) {
          console.error('Path autocomplete error:', err);
          setSuggestions([]);
          setIsVisible(false);
        }
      } finally {
        setIsLoading(false);
      }
    }, [basePath]);

    // Monitor input for @ triggers
    useEffect(() => {
      if (!enabled) {
        setIsVisible(false);
        return;
      }

      const trigger = findAtTrigger(inputValue);

      if (trigger) {
        setAtPosition(trigger.position);
        fetchSuggestions(trigger.prefix);
      } else {
        setIsVisible(false);
        setAtPosition(null);
        setSuggestions([]);
      }
    }, [inputValue, enabled, findAtTrigger, fetchSuggestions]);

    // Cleanup on unmount
    useEffect(() => {
      return () => {
        if (abortRef.current) {
          abortRef.current();
        }
      };
    }, []);

    // Handle selection
    const handleSelect = useCallback((suggestion: PathSuggestion, withWrite: boolean = false) => {
      if (atPosition === null) return;

      const beforeAt = inputValue.substring(0, atPosition);
      const afterPath = inputValue.substring(atPosition).split(/\s/)[0];
      const restOfInput = inputValue.substring(atPosition + afterPath.length);

      // Build new input value
      let newPath = suggestion.path;
      const suffix = withWrite ? ':w' : '';

      // If it's a directory, add trailing slash to continue browsing
      if (suggestion.is_dir && !withWrite) {
        const newValue = `${beforeAt}@${newPath}/`;
        onInputChange(newValue);
        // Don't close - let user continue browsing
        fetchSuggestions(newPath + '/');
        return;
      }

      const newValue = `${beforeAt}@${newPath}${suffix}${restOfInput}`;
      onInputChange(newValue);
      onSelect(newPath, withWrite ? ':w' : undefined);

      setIsVisible(false);
      setSuggestions([]);
      setAtPosition(null);
    }, [atPosition, inputValue, onInputChange, onSelect, fetchSuggestions]);

    // Expose keyboard handler to parent
    useImperativeHandle(ref, () => ({
      handleKeyDown: (e: React.KeyboardEvent): boolean => {
        if (!isVisible || suggestions.length === 0) return false;

        switch (e.key) {
          case 'ArrowDown':
            e.preventDefault();
            setSelectedIndex((prev) => (prev + 1) % suggestions.length);
            setShowWriteSuffix(false);
            return true;

          case 'ArrowUp':
            e.preventDefault();
            setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
            setShowWriteSuffix(false);
            return true;

          case 'ArrowRight':
            // Toggle :w suffix option
            if (suggestions[selectedIndex] && !suggestions[selectedIndex].is_dir) {
              e.preventDefault();
              setShowWriteSuffix((prev) => !prev);
              return true;
            }
            return false;

          case 'Tab':
          case 'Enter':
            e.preventDefault();
            if (suggestions[selectedIndex]) {
              handleSelect(suggestions[selectedIndex], showWriteSuffix);
            }
            return true;

          case 'Escape':
            e.preventDefault();
            setIsVisible(false);
            setSuggestions([]);
            return true;

          default:
            return false;
        }
      },
      isShowing: () => isVisible,
    }), [isVisible, suggestions, selectedIndex, showWriteSuffix, handleSelect]);

    // Scroll selected item into view
    useEffect(() => {
      if (dropdownRef.current && suggestions.length > 0) {
        const selected = dropdownRef.current.querySelector(`[data-index="${selectedIndex}"]`);
        if (selected) {
          selected.scrollIntoView({ block: 'nearest' });
        }
      }
    }, [selectedIndex, suggestions.length]);

    if (!isVisible) return null;

    return (
      <AnimatePresence>
        <motion.div
          ref={dropdownRef}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          transition={{ duration: 0.15 }}
          className="absolute bottom-full left-0 right-0 mb-2 mx-4 bg-gray-800 border border-gray-700
                     rounded-lg shadow-xl overflow-hidden max-h-64 overflow-y-auto z-50"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 bg-gray-700/50 border-b border-gray-700">
            <span className="text-xs text-gray-400">
              File suggestions {isLoading && '(loading...)'}
            </span>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span>Tab to select</span>
              <span className="text-gray-600">|</span>
              <span>Right for :w</span>
              <button
                onClick={() => setIsVisible(false)}
                className="p-0.5 hover:bg-gray-600 rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Suggestions list */}
          <div className="py-1">
            {suggestions.map((suggestion, index) => {
              const Icon = getFileIcon(suggestion.name, suggestion.is_dir);
              const isSelected = index === selectedIndex;

              return (
                <div
                  key={suggestion.path}
                  data-index={index}
                  onClick={() => handleSelect(suggestion, showWriteSuffix && isSelected)}
                  onMouseEnter={() => {
                    setSelectedIndex(index);
                    setShowWriteSuffix(false);
                  }}
                  className={`
                    flex items-center gap-2 px-3 py-1.5 cursor-pointer
                    ${isSelected ? 'bg-blue-600/30 text-blue-100' : 'text-gray-300 hover:bg-gray-700/50'}
                  `}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 ${suggestion.is_dir ? 'text-amber-400' : 'text-gray-400'}`} />
                  <span className="flex-1 truncate text-sm">{suggestion.name}</span>
                  {isSelected && !suggestion.is_dir && (
                    <span className={`text-xs ${showWriteSuffix ? 'text-green-400' : 'text-gray-500'}`}>
                      {showWriteSuffix ? ':w (write)' : '(read)'}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {suggestions.length === 0 && !isLoading && (
            <div className="px-3 py-4 text-center text-gray-500 text-sm">
              No files found
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    );
  }
);

export default PathAutocomplete;
