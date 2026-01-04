/**
 * Workspace Browser State Machine Hook
 *
 * Implements the state machine defined in data-model.md for managing
 * workspace browser loading, error, and success states reliably.
 *
 * Uses discriminated unions to prevent invalid state combinations.
 *
 * @see specs/001-fix-workspace-browser/data-model.md
 */

import { useCallback, useReducer } from 'react';
import type { WorkspaceFileInfo } from '../types';
import type {
  WorkspaceBrowserState,
  WorkspaceAction,
  WorkspacesResponse,
  WorkspaceErrorType,
} from '../types/workspaceState';

/**
 * Initial state for the workspace browser.
 */
const initialState: WorkspaceBrowserState = { status: 'idle' };

/**
 * State machine reducer for workspace browser.
 * Ensures only valid state transitions occur.
 */
function workspaceBrowserReducer(
  state: WorkspaceBrowserState,
  action: WorkspaceAction
): WorkspaceBrowserState {
  switch (action.type) {
    case 'OPEN_MODAL':
      // Can only open from idle state
      if (state.status === 'idle') {
        return { status: 'loading-workspaces' };
      }
      return state;

    case 'CLOSE_MODAL':
      // Can close from any state
      return { status: 'idle' };

    case 'WORKSPACES_LOADED':
      // Transition from loading-workspaces to loading-files
      if (state.status === 'loading-workspaces') {
        return {
          status: 'loading-files',
          workspaces: action.workspaces,
          selectedAgent: null,
        };
      }
      return state;

    case 'WORKSPACES_ERROR':
      // Transition from loading-workspaces to error
      if (state.status === 'loading-workspaces') {
        return {
          status: 'error',
          error: action.error,
          errorType: action.errorType,
        };
      }
      return state;

    case 'SELECT_AGENT':
      // Can select agent from loading-files or ready state
      if (state.status === 'loading-files') {
        return {
          ...state,
          selectedAgent: action.agentId,
        };
      }
      if (state.status === 'ready') {
        // Preserve workspaces, transition to loading-files for new agent
        return {
          status: 'loading-files',
          workspaces: state.workspaces,
          selectedAgent: action.agentId,
        };
      }
      // From error state with last known workspaces
      if (state.status === 'error' && state.lastKnownWorkspaces) {
        return {
          status: 'loading-files',
          workspaces: state.lastKnownWorkspaces,
          selectedAgent: action.agentId,
        };
      }
      return state;

    case 'FILES_LOADED':
      // Transition from loading-files to ready
      if (state.status === 'loading-files' && state.selectedAgent) {
        return {
          status: 'ready',
          workspaces: state.workspaces,
          files: action.files,
          selectedAgent: state.selectedAgent,
          selectedFilePath: null,
          lastRefreshed: Date.now(),
        };
      }
      // Update files in ready state (e.g., from WebSocket events)
      if (state.status === 'ready') {
        return {
          ...state,
          files: action.files,
          lastRefreshed: Date.now(),
        };
      }
      return state;

    case 'FILES_ERROR':
      // Transition from loading-files to error, preserving last known state
      if (state.status === 'loading-files') {
        return {
          status: 'error',
          error: action.error,
          errorType: action.errorType,
          lastKnownWorkspaces: state.workspaces,
        };
      }
      // From ready state, preserve files
      if (state.status === 'ready') {
        return {
          status: 'error',
          error: action.error,
          errorType: action.errorType,
          lastKnownWorkspaces: state.workspaces,
          lastKnownFiles: state.files,
        };
      }
      return state;

    case 'SELECT_FILE':
      // Can only select file in ready state
      if (state.status === 'ready') {
        return {
          ...state,
          selectedFilePath: action.filePath,
        };
      }
      return state;

    case 'REFRESH':
      // Trigger refresh from ready or error state
      if (state.status === 'ready') {
        return {
          status: 'loading-files',
          workspaces: state.workspaces,
          selectedAgent: state.selectedAgent,
        };
      }
      if (state.status === 'error' && state.lastKnownWorkspaces) {
        return {
          status: 'loading-files',
          workspaces: state.lastKnownWorkspaces,
          selectedAgent: null,
        };
      }
      return state;

    case 'FILE_CHANGED':
      // Handle real-time file change from WebSocket
      if (state.status === 'ready') {
        const { file, operation } = action;
        let newFiles: WorkspaceFileInfo[];

        switch (operation) {
          case 'create':
            // Add new file if not already present
            if (!state.files.some((f) => f.path === file.path)) {
              newFiles = [...state.files, file];
            } else {
              // Update existing file (in case of rapid create/modify)
              newFiles = state.files.map((f) =>
                f.path === file.path ? { ...f, ...file } : f
              );
            }
            break;

          case 'modify':
            // Update existing file
            newFiles = state.files.map((f) =>
              f.path === file.path ? { ...f, ...file } : f
            );
            break;

          case 'delete':
            // Remove file from list
            newFiles = state.files.filter((f) => f.path !== file.path);
            // If the deleted file was selected, clear the selection
            if (state.selectedFilePath === file.path) {
              return {
                ...state,
                files: newFiles,
                selectedFilePath: null,
                lastRefreshed: Date.now(),
              };
            }
            break;

          default:
            return state;
        }

        return {
          ...state,
          files: newFiles,
          lastRefreshed: Date.now(),
        };
      }
      return state;

    default:
      return state;
  }
}

/**
 * Hook return type with state and action dispatchers.
 */
interface UseWorkspaceBrowserStateReturn {
  /** Current state of the workspace browser */
  state: WorkspaceBrowserState;
  /** Open the modal and start loading workspaces */
  openModal: () => void;
  /** Close the modal and reset state */
  closeModal: () => void;
  /** Handle successful workspace fetch */
  workspacesLoaded: (workspaces: WorkspacesResponse) => void;
  /** Handle workspace fetch error */
  workspacesError: (error: string, errorType: WorkspaceErrorType) => void;
  /** Select an agent to view their workspace */
  selectAgent: (agentId: string) => void;
  /** Handle successful file fetch */
  filesLoaded: (files: WorkspaceFileInfo[]) => void;
  /** Handle file fetch error */
  filesError: (error: string, errorType: WorkspaceErrorType) => void;
  /** Select a file to view */
  selectFile: (filePath: string) => void;
  /** Trigger a refresh of the current workspace */
  refresh: () => void;
  /** Handle real-time file change from WebSocket */
  fileChanged: (
    file: WorkspaceFileInfo,
    operation: 'create' | 'modify' | 'delete'
  ) => void;
}

/**
 * Custom hook for managing workspace browser state machine.
 *
 * @example
 * ```tsx
 * const {
 *   state,
 *   openModal,
 *   closeModal,
 *   selectAgent,
 *   filesLoaded,
 *   fileChanged,
 * } = useWorkspaceBrowserState();
 *
 * // Check loading state
 * if (state.status === 'loading-workspaces') {
 *   return <LoadingSpinner />;
 * }
 *
 * // Render files
 * if (state.status === 'ready') {
 *   return <FileList files={state.files} />;
 * }
 * ```
 */
export function useWorkspaceBrowserState(): UseWorkspaceBrowserStateReturn {
  const [state, dispatch] = useReducer(workspaceBrowserReducer, initialState);

  const openModal = useCallback(() => {
    dispatch({ type: 'OPEN_MODAL' });
  }, []);

  const closeModal = useCallback(() => {
    dispatch({ type: 'CLOSE_MODAL' });
  }, []);

  const workspacesLoaded = useCallback((workspaces: WorkspacesResponse) => {
    dispatch({ type: 'WORKSPACES_LOADED', workspaces });
  }, []);

  const workspacesError = useCallback(
    (error: string, errorType: WorkspaceErrorType) => {
      dispatch({ type: 'WORKSPACES_ERROR', error, errorType });
    },
    []
  );

  const selectAgent = useCallback((agentId: string) => {
    dispatch({ type: 'SELECT_AGENT', agentId });
  }, []);

  const filesLoaded = useCallback((files: WorkspaceFileInfo[]) => {
    dispatch({ type: 'FILES_LOADED', files });
  }, []);

  const filesError = useCallback((error: string, errorType: WorkspaceErrorType) => {
    dispatch({ type: 'FILES_ERROR', error, errorType });
  }, []);

  const selectFile = useCallback((filePath: string) => {
    dispatch({ type: 'SELECT_FILE', filePath });
  }, []);

  const refresh = useCallback(() => {
    dispatch({ type: 'REFRESH' });
  }, []);

  const fileChanged = useCallback(
    (file: WorkspaceFileInfo, operation: 'create' | 'modify' | 'delete') => {
      dispatch({ type: 'FILE_CHANGED', file, operation });
    },
    []
  );

  return {
    state,
    openModal,
    closeModal,
    workspacesLoaded,
    workspacesError,
    selectAgent,
    filesLoaded,
    filesError,
    selectFile,
    refresh,
    fileChanged,
  };
}

export default useWorkspaceBrowserState;
