import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import { Toaster } from "@/components/ui/sonner";

function App() {
  useEffect(() => {
    // Suppress ResizeObserver errors at console level
    const originalError = console.error;
    console.error = (...args) => {
      if (args[0]?.toString().includes('ResizeObserver')) return;
      originalError.apply(console, args);
    };
    
    return () => {
      console.error = originalError;
    };
  }, []);

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
