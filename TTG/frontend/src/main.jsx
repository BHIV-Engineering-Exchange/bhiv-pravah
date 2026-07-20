import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import App from "./App";
import UserSimPage from "./pages/UserSimPage";
import SimPage from "./pages/SimPage";

ReactDOM.createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/simulate" element={<UserSimPage />} />
      <Route path="/sim" element={<SimPage />} />
    </Routes>
  </BrowserRouter>
);
