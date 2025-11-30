/**
 * ConvergenceAnimation Component
 *
 * Popup notification when consensus is reached.
 * Auto-dismisses and switches to winner-only view.
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Sparkles, ArrowRight } from 'lucide-react';
import { useAgentStore, selectSelectedAgent, selectIsComplete, selectAgents } from '../stores/agentStore';

interface ConvergenceAnimationProps {
  onViewWinner?: () => void;
}

export function ConvergenceAnimation({ onViewWinner }: ConvergenceAnimationProps) {
  const selectedAgent = useAgentStore(selectSelectedAgent);
  const agents = useAgentStore(selectAgents);
  const isComplete = useAgentStore(selectIsComplete);
  const [dismissed, setDismissed] = useState(false);

  const showAnimation = isComplete && selectedAgent && !dismissed;

  // Get winner's model name for display
  const winnerAgent = selectedAgent ? agents[selectedAgent] : null;
  const winnerDisplayName = winnerAgent?.modelName
    ? `${selectedAgent} (${winnerAgent.modelName})`
    : selectedAgent;

  // Auto-dismiss after 5 seconds and switch to winner view
  useEffect(() => {
    if (showAnimation) {
      const timer = setTimeout(() => {
        setDismissed(true);
        onViewWinner?.();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [showAnimation, onViewWinner]);

  // Reset dismissed state when a new session starts
  useEffect(() => {
    if (!isComplete) {
      setDismissed(false);
    }
  }, [isComplete]);

  const handleViewNow = () => {
    setDismissed(true);
    onViewWinner?.();
  };

  return (
    <AnimatePresence>
      {showAnimation && (
        <motion.div
          initial={{ opacity: 0, y: 50, x: '-50%' }}
          animate={{ opacity: 1, y: 0, x: '-50%' }}
          exit={{ opacity: 0, y: 50, x: '-50%' }}
          className="fixed bottom-6 left-1/2 z-50 max-w-lg w-full mx-4"
        >
          {/* Toast Card */}
          <div className="bg-gray-900 border-2 border-yellow-500 rounded-xl p-4 shadow-2xl shadow-yellow-500/20">
            <div className="flex items-center gap-4">
              {/* Icon */}
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.5, repeat: 2 }}
                className="shrink-0"
              >
                <Trophy className="w-10 h-10 text-yellow-500" />
              </motion.div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-bold text-yellow-400 flex items-center gap-2">
                  Consensus Reached!
                  <Sparkles className="w-5 h-5" />
                </h2>
                <p className="text-gray-400 text-sm">
                  Winner: <span className="text-yellow-300 font-medium">{winnerDisplayName}</span>
                </p>
              </div>

              {/* View Winner Button */}
              <button
                onClick={handleViewNow}
                className="shrink-0 flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-500
                         text-white rounded-lg transition-colors font-medium"
              >
                View
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Progress bar for auto-dismiss */}
            <motion.div
              initial={{ width: '100%' }}
              animate={{ width: '0%' }}
              transition={{ duration: 5, ease: 'linear' }}
              className="h-1 bg-yellow-500/50 rounded-full mt-3"
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default ConvergenceAnimation;
