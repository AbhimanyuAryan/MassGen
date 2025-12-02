/**
 * TimelineNode Component
 *
 * Renders a single node on the timeline (answer, vote, or final).
 * Color-coded by type with hover effects and tooltips.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import type { TimelineNode as TimelineNodeType } from '../../types';

interface TimelineNodeProps {
  node: TimelineNodeType;
  x: number;
  y: number;
  size: number;
  onClick?: () => void;
}

// Node colors by type
const nodeColors = {
  answer: {
    fill: 'url(#answerGradient)',
    stroke: '#60A5FA',
    glow: 'rgba(59, 130, 246, 0.4)',
  },
  vote: {
    fill: 'url(#voteGradient)',
    stroke: '#FBBF24',
    glow: 'rgba(245, 158, 11, 0.4)',
  },
  final: {
    fill: 'url(#finalGradient)',
    stroke: '#FDE047',
    glow: 'rgba(234, 179, 8, 0.5)',
  },
};

export function TimelineNode({ node, x, y, size, onClick }: TimelineNodeProps) {
  const [isHovered, setIsHovered] = useState(false);
  const colors = nodeColors[node.type];
  const radius = size / 2;

  // Format timestamp for tooltip
  const formatTime = (timestamp: number) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <g
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Gradient definitions */}
      <defs>
        <linearGradient id="answerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3B82F6" />
          <stop offset="100%" stopColor="#2563EB" />
        </linearGradient>
        <linearGradient id="voteGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#D97706" />
        </linearGradient>
        <linearGradient id="finalGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#EAB308" />
          <stop offset="100%" stopColor="#CA8A04" />
        </linearGradient>
        <filter id={`glow-${node.id}`}>
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Glow effect on hover */}
      {isHovered && (
        <circle
          cx={x}
          cy={y}
          r={radius + 6}
          fill={colors.glow}
          opacity={0.6}
        />
      )}

      {/* Main node circle */}
      <motion.circle
        cx={x}
        cy={y}
        r={radius}
        fill={colors.fill}
        stroke={colors.stroke}
        strokeWidth={2}
        initial={{ scale: 0 }}
        animate={{ scale: isHovered ? 1.15 : 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        filter={node.type === 'final' ? `url(#glow-${node.id})` : undefined}
      />

      {/* Icon inside node */}
      <text
        x={x}
        y={y + 1}
        textAnchor="middle"
        dominantBaseline="middle"
        className="fill-white text-xs font-bold select-none pointer-events-none"
      >
        {node.type === 'answer' && 'A'}
        {node.type === 'vote' && 'V'}
        {node.type === 'final' && '★'}
      </text>

      {/* Label below node */}
      <text
        x={x}
        y={y + radius + 14}
        textAnchor="middle"
        className="fill-gray-400 text-xs font-medium select-none pointer-events-none"
      >
        {node.label}
      </text>

      {/* Tooltip on hover */}
      {isHovered && (
        <g>
          <rect
            x={x + radius + 10}
            y={y - 30}
            width={140}
            height={60}
            rx={6}
            fill="rgba(31, 41, 55, 0.95)"
            stroke="rgba(75, 85, 99, 0.5)"
            strokeWidth={1}
          />
          <text
            x={x + radius + 18}
            y={y - 12}
            className="fill-gray-200 text-xs font-medium"
          >
            {node.label}
          </text>
          <text
            x={x + radius + 18}
            y={y + 4}
            className="fill-gray-400 text-xs"
          >
            {formatTime(node.timestamp)}
          </text>
          {node.type === 'vote' && node.votedFor && (
            <text
              x={x + radius + 18}
              y={y + 20}
              className="fill-amber-400 text-xs"
            >
              → {node.votedFor}
            </text>
          )}
          {node.contextSources.length > 0 && (
            <text
              x={x + radius + 18}
              y={y + 20}
              className="fill-blue-400 text-xs"
            >
              ← {node.contextSources.join(', ')}
            </text>
          )}
        </g>
      )}
    </g>
  );
}

export default TimelineNode;
