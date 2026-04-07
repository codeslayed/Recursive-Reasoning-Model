import { useEffect, useRef } from "react";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { Brain, CheckCircle, AlertCircle, Target } from "lucide-react";

const nodeTypes = {
  custom: ({ data }) => {
    const getIcon = () => {
      switch (data.type) {
        case "decomposition":
          return <Brain className="w-4 h-4" />;
        case "reflection":
          return <AlertCircle className="w-4 h-4" />;
        case "verification":
          return <CheckCircle className="w-4 h-4" />;
        case "synthesis":
          return <Target className="w-4 h-4" />;
        default:
          return <Brain className="w-4 h-4" />;
      }
    };

    const getColor = () => {
      switch (data.type) {
        case "decomposition":
          return "border-blue-600 bg-blue-50";
        case "reflection":
          return "border-amber-500 bg-amber-50";
        case "verification":
          return "border-red-500 bg-red-50";
        case "synthesis":
          return "border-emerald-600 bg-emerald-50";
        default:
          return "border-slate-300 bg-white";
      }
    };

    return (
      <div
        className={`px-4 py-3 rounded-sm border-2 ${getColor()} shadow-sm min-w-[180px]`}
        data-testid={`tree-node-${data.label}`}
      >
        <div className="flex items-center gap-2 mb-1">
          {getIcon()}
          <div className="text-xs uppercase tracking-wider font-mono font-semibold">{data.type}</div>
        </div>
        <div className="text-sm text-slate-700 font-medium">{data.label}</div>
      </div>
    );
  },
};

const ReasoningTree = ({ steps }) => {
  const nodes = [];
  const edges = [];

  // Create nodes from steps
  steps.forEach((step, index) => {
    const nodeId = `node-${index}`;
    nodes.push({
      id: nodeId,
      type: "custom",
      position: {
        x: (index % 2) * 300 + 100,
        y: Math.floor(index / 2) * 150 + 50,
      },
      data: {
        type: step.step_type,
        label: `Step ${index + 1}`,
      },
    });

    // Create edge to previous node
    if (index > 0) {
      edges.push({
        id: `edge-${index}`,
        source: `node-${index - 1}`,
        target: nodeId,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
        },
        style: { strokeWidth: 2, stroke: "#94a3b8" },
      });
    }
  });

  return (
    <div className="w-full h-full" data-testid="reasoning-tree">
      {nodes.length > 0 ? (
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
          <Background color="#e2e8f0" gap={16} />
          <Controls />
        </ReactFlow>
      ) : (
        <div className="flex items-center justify-center h-full text-slate-500 text-sm">
          Reasoning tree will appear here...
        </div>
      )}
    </div>
  );
};

export default ReasoningTree;
