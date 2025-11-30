/**
 * HeaderControls Component
 *
 * Config selector dropdown and session management controls.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, FolderOpen, Users, ChevronDown, RefreshCw, Plus, FileText, Sun, Moon, Monitor } from 'lucide-react';
import type { ConfigInfo, SessionInfo } from '../types';
import { useThemeStore, selectThemeMode, selectSetThemeMode, type ThemeMode } from '../stores/themeStore';

interface HeaderControlsProps {
  currentSessionId: string;
  selectedConfig: string | null;
  onConfigChange: (configPath: string) => void;
  onSessionChange: (sessionId: string) => void;
  onNewSession: () => void;
  onOpenAnswerBrowser: () => void;
  answerCount: number;
}

export function HeaderControls({
  currentSessionId,
  selectedConfig,
  onConfigChange,
  onSessionChange,
  onNewSession,
  onOpenAnswerBrowser,
  answerCount,
}: HeaderControlsProps) {
  const [configs, setConfigs] = useState<ConfigInfo[]>([]);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [defaultConfig, setDefaultConfig] = useState<string | null>(null);
  const [showConfigDropdown, setShowConfigDropdown] = useState(false);
  const [showSessionDropdown, setShowSessionDropdown] = useState(false);
  const [loading, setLoading] = useState(true);

  // Theme state
  const themeMode = useThemeStore(selectThemeMode);
  const setThemeMode = useThemeStore(selectSetThemeMode);

  const cycleTheme = () => {
    const modes: ThemeMode[] = ['light', 'dark', 'system'];
    const currentIndex = modes.indexOf(themeMode);
    const nextIndex = (currentIndex + 1) % modes.length;
    setThemeMode(modes[nextIndex]);
  };

  const ThemeIcon = themeMode === 'light' ? Sun : themeMode === 'dark' ? Moon : Monitor;

  // Fetch available configs
  const fetchConfigs = useCallback(async () => {
    try {
      const res = await fetch('/api/configs');
      const data = await res.json();
      setConfigs(data.configs || []);
      setDefaultConfig(data.default);
      if (!selectedConfig && data.default) {
        onConfigChange(data.default);
      }
    } catch (err) {
      console.error('Failed to fetch configs:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedConfig, onConfigChange]);

  // Fetch active sessions
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    }
  }, []);

  useEffect(() => {
    fetchConfigs();
    fetchSessions();
    // Poll sessions every 5 seconds
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, [fetchConfigs, fetchSessions]);

  // Group configs by category
  const groupedConfigs = configs.reduce<Record<string, ConfigInfo[]>>((acc, config) => {
    const cat = config.category || 'root';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(config);
    return acc;
  }, {});

  const selectedConfigName = configs.find(c => c.path === selectedConfig)?.name || 'Select Config';

  return (
    <div className="flex items-center gap-4">
      {/* Config Selector */}
      <div className="relative">
        <button
          onClick={() => {
            setShowConfigDropdown(!showConfigDropdown);
            setShowSessionDropdown(false);
          }}
          className="flex items-center gap-2 px-3 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600
                   rounded-lg border border-gray-300 dark:border-gray-600 text-sm transition-colors"
        >
          <FolderOpen className="w-4 h-4 text-blue-400" />
          <span className="max-w-[200px] truncate">
            {loading ? 'Loading...' : selectedConfigName}
          </span>
          <ChevronDown className={`w-4 h-4 transition-transform ${showConfigDropdown ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence>
          {showConfigDropdown && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute right-0 mt-2 w-80 max-h-[400px] overflow-y-auto
                       bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50"
            >
              {defaultConfig && (
                <div className="p-2 border-b border-gray-200 dark:border-gray-700">
                  <div className="text-xs text-gray-500 mb-1">Default (from CLI)</div>
                  <button
                    onClick={() => {
                      onConfigChange(defaultConfig);
                      setShowConfigDropdown(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded text-sm truncate
                             ${selectedConfig === defaultConfig
                               ? 'bg-blue-600 text-white'
                               : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                  >
                    {configs.find(c => c.path === defaultConfig)?.name || defaultConfig}
                  </button>
                </div>
              )}

              {Object.entries(groupedConfigs).map(([category, categoryConfigs]) => (
                <div key={category} className="p-2 border-b border-gray-200 dark:border-gray-700 last:border-0">
                  <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">
                    {category === 'root' ? 'General' : category}
                  </div>
                  {categoryConfigs.map((config) => (
                    <button
                      key={config.path}
                      onClick={() => {
                        onConfigChange(config.path);
                        setShowConfigDropdown(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded text-sm truncate
                               ${selectedConfig === config.path
                                 ? 'bg-blue-600 text-white'
                                 : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                      title={config.path}
                    >
                      {config.name}
                    </button>
                  ))}
                </div>
              ))}

              {configs.length === 0 && !loading && (
                <div className="p-4 text-center text-gray-500 text-sm">
                  No configs found
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Session Selector */}
      <div className="relative">
        <button
          onClick={() => {
            setShowSessionDropdown(!showSessionDropdown);
            setShowConfigDropdown(false);
          }}
          className="flex items-center gap-2 px-3 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600
                   rounded-lg border border-gray-300 dark:border-gray-600 text-sm transition-colors"
        >
          <Users className="w-4 h-4 text-purple-400" />
          <span>Sessions ({sessions.length})</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${showSessionDropdown ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence>
          {showSessionDropdown && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute right-0 mt-2 w-80 max-h-[300px] overflow-y-auto
                       bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50"
            >
              {/* New Session Button */}
              <div className="p-2 border-b border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => {
                    onNewSession();
                    setShowSessionDropdown(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded text-sm
                           bg-green-600 hover:bg-green-500 text-white transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  New Session
                </button>
              </div>

              {/* Session List */}
              <div className="p-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500">Active Sessions</span>
                  <button
                    onClick={fetchSessions}
                    className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    title="Refresh"
                  >
                    <RefreshCw className="w-3 h-3 text-gray-500" />
                  </button>
                </div>

                {sessions.length === 0 ? (
                  <div className="text-gray-500 text-sm text-center py-2">
                    No active sessions
                  </div>
                ) : (
                  sessions.map((session) => (
                    <button
                      key={session.session_id}
                      onClick={() => {
                        onSessionChange(session.session_id);
                        setShowSessionDropdown(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded text-sm mb-1
                               ${currentSessionId === session.session_id
                                 ? 'bg-purple-600 text-white'
                                 : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs truncate max-w-[180px]">
                          {session.session_id.slice(0, 8)}...
                        </span>
                        <div className="flex items-center gap-2">
                          {session.is_running && (
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                          )}
                          <span className="text-xs text-gray-400">
                            {session.connections} conn
                          </span>
                        </div>
                      </div>
                      {session.question && (
                        <div className="text-xs text-gray-400 truncate mt-1">
                          {session.question}
                        </div>
                      )}
                    </button>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Answers Browser */}
      <button
        onClick={onOpenAnswerBrowser}
        className="flex items-center gap-2 px-3 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600
                 rounded-lg border border-gray-300 dark:border-gray-600 text-sm transition-colors"
        title="Browse Answers"
      >
        <FileText className="w-4 h-4 text-blue-500 dark:text-blue-400" />
        <span>Answers</span>
        {answerCount > 0 && (
          <span className="px-1.5 py-0.5 bg-blue-600 text-white rounded-full text-xs min-w-[1.25rem] text-center">
            {answerCount}
          </span>
        )}
      </button>

      {/* Theme Toggle */}
      <button
        onClick={cycleTheme}
        className="flex items-center gap-2 px-3 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600
                 rounded-lg border border-gray-300 dark:border-gray-600 text-sm transition-colors"
        title={`Theme: ${themeMode} (click to cycle)`}
      >
        <ThemeIcon className="w-4 h-4 text-amber-500 dark:text-yellow-400" />
        <span className="capitalize">{themeMode}</span>
      </button>

      {/* Settings */}
      <button
        className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
        title="Settings"
      >
        <Settings className="w-5 h-5 text-gray-500 dark:text-gray-400" />
      </button>
    </div>
  );
}

export default HeaderControls;
