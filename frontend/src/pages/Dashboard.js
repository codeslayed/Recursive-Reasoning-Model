import { useEffect, useState, useCallback } from "react";
import { api } from "../services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Brain, Clock, Cpu, Layers, TrendingUp, Send, History, Loader2 } from "lucide-react";
import { toast } from "sonner";
import ReasoningTree from "../components/ReasoningTree";

const Dashboard = () => {
  const [query, setQuery] = useState("");
  const [maxDepth, setMaxDepth] = useState(3);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const [steps, setSteps] = useState([]);
  const [metrics, setMetrics] = useState({
    tokens: 0,
    latency: 0,
    depth: 0,
    confidence: 0,
  });
  const [finalAnswer, setFinalAnswer] = useState("");
  const [sessions, setSessions] = useState([]);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
    } catch (error) {
      console.error("Failed to load sessions:", error);
    }
  };

  const handleSubmit = async () => {
    if (!query.trim()) {
      toast.error("Please enter a query");
      return;
    }

    // Close existing WebSocket if any
    if (ws) {
      ws.close();
      setWs(null);
    }

    try {
      setIsProcessing(true);
      setSteps([]);
      setFinalAnswer("");
      setMetrics({ tokens: 0, latency: 0, depth: 0, confidence: 0 });

      // Create session
      const session = await api.createSession(query, maxDepth);
      setCurrentSession(session);

      // Connect WebSocket
      const socket = api.connectWebSocket(session.id);
      setWs(socket);

      socket.onopen = () => {
        toast.success("Connected to reasoning engine");
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "step_start") {
          toast.info(message.data.message);
        } else if (message.type === "step_complete") {
          setSteps((prev) => [...prev, message.data]);
          setMetrics((prev) => ({
            tokens: prev.tokens + (message.data.tokens_used || 0),
            latency: prev.latency + (message.data.latency_ms || 0),
            depth: Math.max(prev.depth, 1),
            confidence: message.data.confidence || prev.confidence,
          }));
        } else if (message.type === "completion") {
          setFinalAnswer(message.data.final_answer);
          setMetrics((prev) => ({
            tokens: message.data.total_tokens,
            latency: message.data.total_latency_ms,
            depth: message.data.recursion_depth,
            confidence: prev.confidence,
          }));
          setIsProcessing(false);
          toast.success("Reasoning complete!");
          loadSessions();
          // Close socket after completion
          setTimeout(() => {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send("close");
              socket.close();
            }
          }, 1000);
        } else if (message.type === "error") {
          toast.error(message.data.message || "An error occurred");
          setIsProcessing(false);
          socket.close();
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        toast.error("Connection error");
        setIsProcessing(false);
      };

      socket.onclose = (event) => {
        console.log("WebSocket closed", event.code, event.reason);
        if (isProcessing) {
          setIsProcessing(false);
        }
      };
    } catch (error) {
      console.error("Failed to start reasoning:", error);
      toast.error("Failed to start reasoning");
      setIsProcessing(false);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const session = await api.getSession(sessionId);
      setCurrentSession(session);
      setSteps(session.steps || []);
      setFinalAnswer(session.final_answer || "");
      setQuery(session.query);
      setMetrics({
        tokens: session.total_tokens || 0,
        latency: session.total_latency_ms || 0,
        depth: session.recursion_depth || 0,
        confidence: session.steps?.length > 0 ? session.steps[session.steps.length - 1].confidence || 0 : 0,
      });
    } catch (error) {
      console.error("Failed to load session:", error);
      toast.error("Failed to load session");
    }
  };

  const getStepBadgeColor = (type) => {
    switch (type) {
      case "decomposition":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "reflection":
        return "bg-amber-100 text-amber-700 border-amber-200";
      case "verification":
        return "bg-red-100 text-red-700 border-red-200";
      case "synthesis":
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar - Session History */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col h-screen fixed left-0 top-0 z-20">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-black tracking-tighter font-heading">ReasonAI</h1>
          </div>
        </div>
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-slate-500 mb-3">
              <History className="w-3 h-3" />
              <span>Session History</span>
            </div>
            {sessions.map((session) => (
              <button
                key={session.id}
                data-testid={`session-${session.id}`}
                onClick={() => loadSession(session.id)}
                className={`w-full text-left p-3 rounded-sm border text-sm duration-150 ease-out ${
                  currentSession?.id === session.id
                    ? "border-blue-600 bg-blue-50 shadow-sm"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <div className="font-medium text-slate-900 truncate mb-1">{session.query}</div>
                <div className="text-xs text-slate-600">
                  {new Date(session.created_at).toLocaleDateString()}
                </div>
                <Badge
                  className={`mt-2 text-[10px] font-mono tracking-wider ${
                    session.status === "completed" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                  }`}
                >
                  {session.status}
                </Badge>
              </button>
            ))}
          </div>
        </ScrollArea>
      </aside>

      {/* Main Content */}
      <div className="ml-64 flex flex-col h-screen overflow-hidden bg-slate-50 flex-1">
        {/* Header */}
        <header className="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between shrink-0 z-10">
          <div className="flex items-center gap-4 flex-1">
            <Input
              data-testid="query-input"
              placeholder="Enter your complex query..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !isProcessing && handleSubmit()}
              className="flex-1 max-w-2xl border-slate-200 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 rounded-sm"
              disabled={isProcessing}
            />
            <Button
              data-testid="submit-query-button"
              onClick={handleSubmit}
              disabled={isProcessing}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-sm px-6"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Reason
                </>
              )}
            </Button>
          </div>
          <div className="flex items-center gap-4 ml-6">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Max Depth:</span>
              <span className="text-sm font-mono font-semibold text-slate-900">{maxDepth}</span>
            </div>
            <Slider
              data-testid="max-depth-slider"
              value={[maxDepth]}
              onValueChange={(value) => setMaxDepth(value[0])}
              min={1}
              max={5}
              step={1}
              className="w-32"
              disabled={isProcessing}
            />
          </div>
        </header>

        {/* Metrics Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-200 border-b border-slate-200">
          <div data-testid="metrics-tokens" className="bg-white p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2 text-slate-600">
              <Cpu className="w-4 h-4" />
              <span className="text-xs uppercase tracking-wider">Tokens</span>
            </div>
            <div className="text-2xl font-black tracking-tighter font-heading">{metrics.tokens.toLocaleString()}</div>
          </div>
          <div data-testid="metrics-latency" className="bg-white p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2 text-slate-600">
              <Clock className="w-4 h-4" />
              <span className="text-xs uppercase tracking-wider">Latency</span>
            </div>
            <div className="text-2xl font-black tracking-tighter font-heading">{(metrics.latency / 1000).toFixed(2)}s</div>
          </div>
          <div data-testid="metrics-depth" className="bg-white p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2 text-slate-600">
              <Layers className="w-4 h-4" />
              <span className="text-xs uppercase tracking-wider">Depth</span>
            </div>
            <div className="text-2xl font-black tracking-tighter font-heading">{metrics.depth}</div>
          </div>
          <div data-testid="metrics-confidence" className="bg-white p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2 text-slate-600">
              <TrendingUp className="w-4 h-4" />
              <span className="text-xs uppercase tracking-wider">Confidence</span>
            </div>
            <div className="text-2xl font-black tracking-tighter font-heading">{(metrics.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>

        {/* Workspace - Split View */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Reasoning Steps */}
          <div className="w-1/3 min-w-[350px] max-w-[500px] border-r border-slate-200 bg-white overflow-y-auto p-6 flex flex-col gap-4">
            <h2 className="text-xl font-bold tracking-tight font-heading">Live Reasoning Steps</h2>
            {steps.length === 0 && !isProcessing && (
              <div className="text-sm text-slate-600">Submit a query to start reasoning...</div>
            )}
            {steps.length === 0 && isProcessing && (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                Initializing reasoning engine...
              </div>
            )}
            <Accordion type="multiple" className="space-y-3">
              {steps.map((step, index) => (
                <AccordionItem
                  key={step.id || index}
                  value={`step-${index}`}
                  data-testid={`reasoning-step-${index}`}
                  className={`border border-slate-200 rounded-sm bg-white reasoning-step-${step.step_type}`}
                >
                  <AccordionTrigger className="px-4 py-3 hover:bg-slate-50 duration-150 ease-out">
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-3">
                        <Badge className={`text-[10px] font-mono tracking-wider uppercase ${getStepBadgeColor(step.step_type)}`}>
                          {step.step_type}
                        </Badge>
                        <span className="text-sm font-medium text-slate-900">Step {index + 1}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs font-mono text-slate-600">
                        <span>{step.tokens_used} tokens</span>
                        <span>{step.latency_ms}ms</span>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="px-4 py-3 border-t border-slate-100">
                    <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{step.content}</div>
                    {step.confidence > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-100">
                        <span className="text-xs font-mono text-slate-600">Confidence: {(step.confidence * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>

          {/* Right Panel - Tree Visualization & Final Answer */}
          <div className="flex-1 relative bg-slate-50 overflow-hidden flex flex-col">
            <div className="flex-1 tree-canvas-bg">
              <ReasoningTree steps={steps} />
            </div>

            {/* Final Answer Card */}
            {finalAnswer && (
              <div className="p-6 bg-white border-t border-slate-200 max-h-[40%] overflow-y-auto">
                <div className="flex items-center gap-2 mb-3">
                  <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200 text-[10px] font-mono tracking-wider uppercase">
                    Final Answer
                  </Badge>
                </div>
                <div data-testid="final-answer" className="text-base leading-relaxed text-slate-900 whitespace-pre-wrap">
                  {finalAnswer}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
