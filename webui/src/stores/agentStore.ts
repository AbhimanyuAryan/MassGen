/**
 * Zustand Store for MassGen Agent State Management
 *
 * Manages all agent state, votes, and coordination events.
 * Updates from WebSocket events are processed here.
 */

import { create } from 'zustand';
import type {
  AgentRound,
  AgentState,
  AgentStatus,
  Answer,
  FileInfo,
  SessionState,
  ToolCallInfo,
  ViewMode,
  VoteResults,
  WSEvent,
} from '../types';

interface AgentStore extends SessionState {
  // Actions
  initSession: (sessionId: string, question: string, agents: string[], theme: string, agentModels?: Record<string, string>) => void;
  updateAgentContent: (agentId: string, content: string, contentType: string) => void;
  updateAgentStatus: (agentId: string, status: AgentStatus) => void;
  addOrchestratorEvent: (event: string) => void;
  updateVoteDistribution: (votes: Record<string, number>) => void;
  recordVote: (voterId: string, targetId: string, reason: string) => void;
  setConsensus: (winnerId: string) => void;
  setFinalAnswer: (answer: string, voteResults: VoteResults, selectedAgent: string) => void;
  addAnswer: (answer: Answer) => void;
  addFileChange: (agentId: string, file: FileInfo) => void;
  addToolCall: (agentId: string, toolCall: ToolCallInfo) => void;
  updateToolResult: (agentId: string, toolId: string | undefined, result: string, success: boolean) => void;
  setError: (message: string) => void;
  setComplete: (isComplete: boolean) => void;
  setViewMode: (mode: ViewMode) => void;
  startNewRound: (agentId: string, roundType: 'answer' | 'vote') => void;
  setAgentRound: (agentId: string, roundId: string) => void;
  reset: () => void;
  processWSEvent: (event: WSEvent) => void;
}

const initialState: SessionState = {
  sessionId: '',
  question: '',
  agents: {},
  agentOrder: [],
  answers: [],
  voteDistribution: {},
  selectedAgent: undefined,
  finalAnswer: undefined,
  orchestratorEvents: [],
  isComplete: false,
  error: undefined,
  theme: 'dark',
  viewMode: 'coordination',
};

const createAgentState = (id: string, modelName?: string): AgentState => {
  const initialRoundId = `${id}-round-0`;
  return {
    id,
    modelName,
    status: 'waiting',
    content: [],
    currentContent: '',
    rounds: [{
      id: initialRoundId,
      roundNumber: 0,
      type: 'answer',
      label: 'current',
      content: '',
      startTimestamp: Date.now(),
    }],
    currentRoundId: initialRoundId,
    answerCount: 0,
    voteCount: 0,
    files: [],
    toolCalls: [],
  };
};

export const useAgentStore = create<AgentStore>((set, get) => ({
  ...initialState,

  initSession: (sessionId, question, agents, theme, agentModels) => {
    const agentStates: Record<string, AgentState> = {};
    agents.forEach((id) => {
      agentStates[id] = createAgentState(id, agentModels?.[id]);
    });

    set({
      sessionId,
      question,
      agents: agentStates,
      agentOrder: agents,
      answers: [],
      theme,
      isComplete: false,
      error: undefined,
      voteDistribution: {},
      selectedAgent: undefined,
      finalAnswer: undefined,
      orchestratorEvents: [],
      viewMode: 'coordination',
    });
  },

  updateAgentContent: (agentId, content, contentType) => {
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;

      // Increment answer count if this looks like a new answer
      const newAnswerCount =
        contentType === 'status' && content.includes('new_answer')
          ? agent.answerCount + 1
          : agent.answerCount;

      // Update current round's content
      const updatedRounds = agent.rounds.map((round) =>
        round.id === agent.currentRoundId
          ? { ...round, content: round.content + content }
          : round
      );

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            content: [...agent.content, content],
            currentContent: agent.currentContent + content,
            rounds: updatedRounds,
            answerCount: newAnswerCount,
          },
        },
      };
    });
  },

  updateAgentStatus: (agentId, status) => {
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            status,
          },
        },
      };
    });
  },

  addOrchestratorEvent: (event) => {
    set((state) => ({
      orchestratorEvents: [...state.orchestratorEvents, event],
    }));
  },

  updateVoteDistribution: (votes) => {
    set({ voteDistribution: votes });
  },

  recordVote: (voterId, targetId, reason) => {
    set((state) => {
      const agent = state.agents[voterId];
      if (!agent) return state;

      // Update vote distribution
      const newDistribution = { ...state.voteDistribution };
      newDistribution[targetId] = (newDistribution[targetId] || 0) + 1;

      return {
        agents: {
          ...state.agents,
          [voterId]: {
            ...agent,
            voteTarget: targetId,
            voteReason: reason,
          },
        },
        voteDistribution: newDistribution,
      };
    });
  },

  setConsensus: (winnerId) => {
    set({ selectedAgent: winnerId });
  },

  setFinalAnswer: (answer, _voteResults, selectedAgent) => {
    set({
      finalAnswer: answer,
      selectedAgent,
      isComplete: true,
    });
  },

  addAnswer: (answer) => {
    set((state) => {
      // Also update the agent's answer count
      const agent = state.agents[answer.agentId];
      const updatedAgents = agent
        ? {
            ...state.agents,
            [answer.agentId]: {
              ...agent,
              answerCount: Math.max(agent.answerCount, answer.answerNumber),
            },
          }
        : state.agents;

      return {
        answers: [...state.answers, answer],
        agents: updatedAgents,
      };
    });
  },

  addFileChange: (agentId, file) => {
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            files: [...agent.files, file],
          },
        },
      };
    });
  },

  addToolCall: (agentId, toolCall) => {
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            toolCalls: [...agent.toolCalls, toolCall],
          },
        },
      };
    });
  },

  updateToolResult: (agentId, toolId, result, success) => {
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;

      const toolCalls = agent.toolCalls.map((tc) => {
        if (tc.id === toolId || (!toolId && tc.result === undefined)) {
          return { ...tc, result, success };
        }
        return tc;
      });

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            toolCalls,
          },
        },
      };
    });
  },

  setError: (message) => {
    set({ error: message });
  },

  setComplete: (isComplete) => {
    set({ isComplete });
  },

  setViewMode: (mode) => {
    set({ viewMode: mode });
  },

  startNewRound: (agentId, roundType) => {
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;

      // Calculate new round number
      const existingRoundsOfType = agent.rounds.filter(r => r.type === roundType).length;
      const agentIndex = state.agentOrder.indexOf(agentId) + 1;
      const newRoundNumber = existingRoundsOfType + 1;

      // Generate label like "answer1.1" or "vote1"
      const label = roundType === 'answer'
        ? `answer${agentIndex}.${newRoundNumber}`
        : `vote${newRoundNumber}`;

      // Close previous round
      const now = Date.now();
      const newRoundId = `${agentId}-round-${agent.rounds.length}`;

      const updatedRounds = agent.rounds.map((round) =>
        round.id === agent.currentRoundId && !round.endTimestamp
          ? { ...round, endTimestamp: now }
          : round
      );

      // Create new round
      const newRound: AgentRound = {
        id: newRoundId,
        roundNumber: newRoundNumber,
        type: roundType,
        label,
        content: '',
        startTimestamp: now,
      };

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            rounds: [...updatedRounds, newRound],
            currentRoundId: newRoundId,
            currentContent: '', // Reset current content for new round
            voteCount: roundType === 'vote' ? agent.voteCount + 1 : agent.voteCount,
          },
        },
      };
    });
  },

  setAgentRound: (agentId, roundId) => {
    set((state) => {
      const agent = state.agents[agentId];
      if (!agent) return state;

      const round = agent.rounds.find(r => r.id === roundId);
      if (!round) return state;

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            currentRoundId: roundId,
            currentContent: round.content,
          },
        },
      };
    });
  },

  reset: () => {
    set(initialState);
  },

  // Process WebSocket events
  processWSEvent: (event) => {
    const store = get();

    switch (event.type) {
      case 'init':
        if ('agents' in event && 'question' in event) {
          store.initSession(
            event.session_id,
            event.question,
            event.agents,
            'theme' in event ? event.theme : 'dark',
            'agent_models' in event ? (event as { agent_models: Record<string, string> }).agent_models : undefined
          );
        }
        break;

      case 'agent_content':
        if ('agent_id' in event && 'content' in event) {
          store.updateAgentContent(
            event.agent_id,
            event.content,
            'content_type' in event ? event.content_type : 'thinking'
          );
        }
        break;

      case 'agent_status':
        if ('agent_id' in event && 'status' in event) {
          store.updateAgentStatus(event.agent_id, event.status as AgentStatus);
        }
        break;

      case 'orchestrator_event':
        if ('event' in event) {
          store.addOrchestratorEvent(event.event);
        }
        break;

      case 'vote_cast':
        if ('voter_id' in event && 'target_id' in event) {
          store.recordVote(
            event.voter_id,
            event.target_id,
            'reason' in event ? event.reason : ''
          );
        }
        break;

      case 'vote_distribution':
        if ('votes' in event) {
          store.updateVoteDistribution(event.votes);
        }
        break;

      case 'consensus_reached':
        if ('winner_id' in event) {
          store.setConsensus(event.winner_id);
        }
        break;

      case 'final_answer':
        if ('answer' in event) {
          store.setFinalAnswer(
            event.answer,
            'vote_results' in event ? event.vote_results : {},
            'selected_agent' in event ? event.selected_agent : ''
          );
        }
        break;

      case 'new_answer':
        if ('agent_id' in event && 'content' in event) {
          const newAnswerEvent = event as {
            agent_id: string;
            content: string;
            answer_id?: string;
            answer_number?: number;
            timestamp: number;
          };
          // Start a new answer round for this agent
          store.startNewRound(newAnswerEvent.agent_id, 'answer');
          store.addAnswer({
            id: newAnswerEvent.answer_id ?? `${newAnswerEvent.agent_id}-${Date.now()}`,
            agentId: newAnswerEvent.agent_id,
            answerNumber: newAnswerEvent.answer_number ?? 1,
            content: newAnswerEvent.content,
            timestamp: newAnswerEvent.timestamp,
            votes: 0,
          });
        }
        break;

      case 'restart':
        // When an agent restarts, start a new answer round
        if ('reason' in event) {
          // The restart affects all agents - start new rounds for each
          const agentOrder = get().agentOrder;
          agentOrder.forEach((agentId) => {
            store.startNewRound(agentId, 'answer');
          });
        }
        break;

      case 'file_change':
        if ('agent_id' in event && 'path' in event) {
          store.addFileChange(event.agent_id, {
            path: event.path,
            operation: 'operation' in event ? event.operation : 'create',
            timestamp: event.timestamp,
            contentPreview: 'content_preview' in event ? event.content_preview : undefined,
          });
        }
        break;

      case 'tool_call':
        if ('agent_id' in event && 'tool_name' in event) {
          store.addToolCall(event.agent_id, {
            id: 'tool_id' in event ? event.tool_id : undefined,
            name: event.tool_name,
            args: 'tool_args' in event ? event.tool_args : {},
            timestamp: event.timestamp,
          });
        }
        break;

      case 'tool_result':
        if ('agent_id' in event && 'result' in event) {
          store.updateToolResult(
            event.agent_id,
            'tool_id' in event ? event.tool_id : undefined,
            event.result,
            'success' in event ? event.success : true
          );
        }
        break;

      case 'error':
        if ('message' in event) {
          store.setError(event.message);
        }
        break;

      case 'done':
      case 'coordination_complete':
        store.setComplete(true);
        break;

      case 'state_snapshot':
        // Handle full state snapshot for late-joining clients
        if ('agents' in event && Array.isArray(event.agents)) {
          store.initSession(
            event.session_id,
            'question' in event ? (event as { question: string }).question : '',
            event.agents,
            'theme' in event ? (event as { theme: string }).theme : 'dark'
          );
        }
        break;

      default:
        // Ignore unknown events (like keepalive)
        break;
    }
  },
}));

// Selectors
export const selectAgents = (state: AgentStore) => state.agents;
export const selectAgentOrder = (state: AgentStore) => state.agentOrder;
export const selectAnswers = (state: AgentStore) => state.answers;
export const selectVoteDistribution = (state: AgentStore) => state.voteDistribution;
export const selectSelectedAgent = (state: AgentStore) => state.selectedAgent;
export const selectFinalAnswer = (state: AgentStore) => state.finalAnswer;
export const selectIsComplete = (state: AgentStore) => state.isComplete;
export const selectQuestion = (state: AgentStore) => state.question;
export const selectOrchestratorEvents = (state: AgentStore) => state.orchestratorEvents;
export const selectViewMode = (state: AgentStore) => state.viewMode;
