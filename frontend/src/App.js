import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import { Toaster } from "@/components/ui/sonner";

// Suppress ResizeObserver errors (cosmetic only, doesn't affect functionality)
if (typeof window !== 'undefined') {
  const resizeObserverErr = window.console.error;
  window.console.error = (...args) => {
    if (args[0]?.includes?.('ResizeObserver')) return;
    resizeObserverErr(...args);
  };
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
