import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { theme } from "./theme";

createRoot(document.getElementById("root")!).render(
  <StrictMode><ThemeProvider theme={theme}><CssBaseline /><BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}><App /></BrowserRouter></ThemeProvider></StrictMode>,
);
