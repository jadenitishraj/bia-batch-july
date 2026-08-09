// Starts the React app and puts it inside the page.

import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App.jsx";
import "./styles/base.css";
import "./styles/controls.css";
import "./styles/sidebar.css";
import "./styles/notes.css";
import "./styles/chat.css";
import "./styles/trace.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
